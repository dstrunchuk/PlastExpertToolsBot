from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import ContextTypes
import os, json
import pandas as pd
from datetime import datetime
from handlers.database import get_tool_by_id, update_tool, log_action, get_all_foremen, get_all_users, get_all_tools, get_tool_history
import re

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
TOOLS_PATH = os.path.join(DATA_DIR, "tools.json")
USERS_PATH = os.path.join(DATA_DIR, "users.json")
FOREMEN_PATH = os.path.join(DATA_DIR, "foremen.json")
PENDING_PATH = os.path.join(DATA_DIR, "pending.json")

def load_json(path):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def log_action(user_id, action, tool):
    users = load_json(USERS_PATH)
    user = next((u for u in users if u["id"] == user_id), None)
    user_name = user.get("name", "Неизвестный пользователь") if user else "Неизвестный пользователь"

    log = load_json(PENDING_PATH)

    log.append({
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "user_id": user_id,
        "user_name": user_name,
        "action": action,
        "tool_id": tool.get("id"),
        "tool_name": tool.get("name"),
        "object": tool.get("object"),
        "responsible": tool.get("responsible", "Нет"),
        "responsible_id": tool.get("responsible_id", "Нет"),
        "action_description": f"{user_name} -> {action} [{tool.get('name')}]"
    })

    save_json(PENDING_PATH, log)

async def handle_tool_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    data = query.data
    parts = data.split(":")
    action = parts[0]
    tool_id = parts[1]

    tool = await get_tool_by_id(tool_id)
    if not tool:
        await query.edit_message_text("Инструмент не найден.")
        return

    users = await get_all_users()
    foremen = await get_all_foremen()
    user = next((u for u in users if u["id"] == user_id), None)

    if action == "take":
        if user:
            tool["responsible"] = user["name"]
            tool["responsible_id"] = user_id
            await update_tool(tool_id, tool)
            await log_action(user_id, "Стал ответственным", tool)
            await send_success_message(query, f"Вы стали ответственным за {tool['name']}.")

    elif action == "store":
        tool["responsible"] = None
        tool["responsible_id"] = None
        tool["object"] = "Ladu"
        await update_tool(tool_id, tool)
        await log_action(user_id, "Оставил на складе", tool)
        await send_success_message(query, f"Инструмент {tool['name']} возвращен на склад.")

    elif action == "request":
        responsible_id = tool.get("responsible_id")
        if responsible_id:
            responsible_user = next((u for u in users if u["id"] == responsible_id), None)
            if responsible_user:
                try:
                    await context.bot.send_message(
                        chat_id=responsible_id,
                        text=f"🔔 Пользователь {user['name']} хочет получить у вас инструмент *{tool['name']}* (ID: {tool.get('id', 'Без ID')}).",
                        parse_mode="Markdown"
                    )
                    await query.edit_message_text(f"Запрос на передачу инструмента отправлен {responsible_user['name']}.")
                except Exception as e:
                    print(f"Ошибка при отправке запроса: {e}")
                    await query.edit_message_text(f"Не удалось отправить запрос ответственному ({responsible_user['name']}).")
            else:
                await query.edit_message_text("Ответственный пользователь не найден.")
        else:
            await query.edit_message_text("Инструмент не имеет текущего ответственного.")

    elif action == "transfer":
        buttons = []
        for person in foremen:
            if person["role"] == "Ответственный":
                buttons.append([
                    InlineKeyboardButton(person["name"], callback_data=f"confirm_transfer:{tool_id}:{person['id']}")
                ])
        await query.edit_message_text("Кому передать инструмент?", reply_markup=InlineKeyboardMarkup(buttons))

    elif action == "assign":
        buttons = []
        for person in foremen:
            buttons.append([
                InlineKeyboardButton(person["name"], callback_data=f"confirm_assign:{tool_id}:{person['id']}")
            ])
        await query.edit_message_text("Кого назначить ответственным?", reply_markup=InlineKeyboardMarkup(buttons))

    elif action == "confirm_transfer":
        _, tool_id, target_id = parts
        new_resp = next((f for f in foremen if str(f["id"]) == target_id), None)
        if new_resp:
            tool["responsible"] = new_resp["name"]
            tool["responsible_id"] = new_resp["id"]
            await update_tool(tool_id, tool)
            await log_action(user_id, f"Передал {tool['name']} → {new_resp['name']}", tool)
            await send_success_message(query, f"Инструмент {tool['name']} передан {new_resp['name']}.")
        else:
            await query.edit_message_text("Не удалось передать инструмент.")

    elif action == "confirm_assign":
        _, tool_id, target_id = parts
        new_resp = next((f for f in foremen if str(f["id"]) == target_id), None)
        if new_resp:
            tool["responsible"] = new_resp["name"]
            tool["responsible_id"] = new_resp["id"]
            await update_tool(tool_id, tool)
            await log_action(user_id, f"Назначил {new_resp['name']} ответственным", tool)
            await send_success_message(query, f"{new_resp['name']} назначен ответственным за {tool['name']}.")
        else:
            await query.edit_message_text("Не удалось назначить ответственного.")

    elif action == "export":
        await export_pending_to_excel(update, context)

    elif action == "export":
        history = await get_tool_history(tool_id)

        if not history:
            await query.edit_message_text("История для этого инструмента пуста.")
            return

        df = pd.DataFrame(history)
        filename = f"history_tool_{tool_id}.xlsx"
        df.to_excel(filename, index=False)

        await query.message.reply_document(InputFile(filename), caption=f"История инструмента ID {tool_id}")

        await query.edit_message_text(f"Экспорт истории инструмента ID {tool_id} завершён.")

    else:
        await query.edit_message_text("Неизвестное действие.")

async def update_tool_card(query, tool: dict, user_id: int):
    users = load_json(USERS_PATH)
    user = next((u for u in users if u["id"] == user_id), None)
    role = user.get("role", "Ответственный") if user else "Ответственный"

    text = create_tool_card_text(tool)
    buttons = generate_action_buttons(tool, role)
    reply_markup = InlineKeyboardMarkup(buttons) if buttons else None

    await query.edit_message_text(text=text, parse_mode="Markdown", reply_markup=reply_markup)

async def process_tool_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    user_id = update.effective_user.id
    user = await get_user_by_id(user_id)
    role = user.get("role", "Ответственный") if user else "Ответственный"

    user_message = update.message.text.strip()
    tools = await get_all_tools()

    found_tools = []

    # Ищем по ID
    for tool in tools:
        if str(tool.get("id")) == user_message:
            found_tools = [tool]
            break

    # Ищем по названию
    if not found_tools:
        for tool in tools:
            if tool.get("name") and user_message.lower() in tool["name"].lower():
                found_tools.append(tool)

    # Удаляем сообщение пользователя сразу
    try:
        await update.message.delete()
    except Exception as e:
        print(f"Не удалось удалить сообщение поиска: {e}")

    if not found_tools:
        await update.effective_chat.send_message(
            "Инструмент не найден.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("◀️ Главное меню", callback_data="main_back")]
            ])
        )
        return

    if len(found_tools) == 1:
        tool = found_tools[0]
        text = create_tool_card_text(tool)

        # Генерация кнопок действий
        buttons = generate_action_buttons(tool, role)

        # Плюс кнопка История
        buttons.insert(0, [InlineKeyboardButton("🗂 История", callback_data=f"export_one:{tool.get('id')}")])

        await update.effective_chat.send_message(
            text=text,
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    else:
        message = "Найдено несколько инструментов:\n\n"
        keyboard = []
        for idx, tool in enumerate(found_tools):
            message += f"{idx+1}. {tool.get('name', 'Без названия')} (ID: {tool.get('id', 'Нет ID')})\n"
            keyboard.append([
                InlineKeyboardButton(f"{tool.get('name', 'Без названия')}", callback_data=f"view_tool:{tool.get('id')}")
            ])
        
        keyboard.append([InlineKeyboardButton("◀️ Главное меню", callback_data="main_back")])

        await update.effective_chat.send_message(
            text=message,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
async def show_tool_card(update: Update, tool: dict):
    name = tool.get("name", "Без названия")
    tool_id = tool.get("id", "Нет ID")
    obj = tool.get("object", "Не указан")
    responsible = tool.get("responsible", "Никто")
    status = "На складе" if obj.lower() == "ladu" else "На объекте"

    text = (f"*Название:* {name}\n"
            f"*ID:* {tool_id}\n"
            f"*Объект:* {obj}\n"
            f"*Ответственный:* {responsible}\n"
            f"*Статус:* {status}")

    await update.message.reply_text(text, parse_mode="Markdown")

async def show_multiple_tools(update: Update, tools: list):
    keyboard = []
    for tool in tools:
        button_text = f"{tool.get('name', 'Без названия')} (ID: {tool.get('id', 'нет')})"
        callback_data = f"view_tool:{tool.get('id')}"
        keyboard.append([[
            InlineKeyboardButton(button_text, callback_data=callback_data)
        ]])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Найдено несколько инструментов:", reply_markup=reply_markup)

async def handle_view_tool(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    tools = load_json(TOOLS_PATH)
    tool_id = query.data.split(":")[1]
    tool = next((t for t in tools if str(t.get("id")) == tool_id), None)

    if not tool:
        await query.edit_message_text("Инструмент не найден.")
        return

    user_id = query.from_user.id
    users = load_json(USERS_PATH)
    user = next((u for u in users if u["id"] == user_id), None)
    role = user.get("role", "Ответственный") if user else "Ответственный"

    text = create_tool_card_text(tool)
    buttons = generate_action_buttons(tool, role)
    reply_markup = InlineKeyboardMarkup(buttons) if buttons else None

    await query.edit_message_text(text=text, parse_mode="Markdown", reply_markup=reply_markup)

async def handle_view_tool_by_index(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    users = load_json(USERS_PATH)
    tools = load_json(TOOLS_PATH)

    try:
        index = int(query.data.split(":")[1])
        tool = tools[index]
    except (IndexError, ValueError):
        await query.edit_message_text("Инструмент не найден.")
        return

    user = next((u for u in users if u["id"] == user_id), None)
    role = user.get("role", "Ответственный") if user else "Ответственный"

    text = create_tool_card_text(tool)
    buttons = generate_action_buttons(tool, role)
    reply_markup = InlineKeyboardMarkup(buttons) if buttons else None

    await query.edit_message_text(text=text, parse_mode="Markdown", reply_markup=reply_markup)

def generate_action_buttons(tool: dict, role: str):
    buttons = []
    responsible_id = tool.get("responsible_id")

    # Ответственный или Админ
    if role in ["Ответственный", "Админ"]:
        if not responsible_id:
            buttons.append([InlineKeyboardButton("✅ Стать ответственным", callback_data=f"take:{tool['id']}")])
        elif responsible_id == tool.get("responsible_id"):
            buttons.append([
                InlineKeyboardButton("📤 Передать", callback_data=f"transfer:{tool['id']}"),
                InlineKeyboardButton("🏬 Оставить на складе", callback_data=f"store:{tool['id']}")
            ])
        else:
            buttons.append([InlineKeyboardButton("📥 Запросить передачу", callback_data=f"request:{tool['id']}")])

    # Супервайзер или Босс
    if role in ["Супервайзер", "Босс"]:
        buttons.append([
            InlineKeyboardButton("👤 Назначить ответственного", callback_data=f"assign:{tool['id']}"),
            InlineKeyboardButton("🏬 Оставить на складе", callback_data=f"store:{tool['id']}")
        ])
        buttons.append([InlineKeyboardButton("🗂 История", callback_data=f"export:{tool['id']}")])

    # Всегда кнопка "Главное меню"
    buttons.append([InlineKeyboardButton("◀️ Главное меню", callback_data="main_back")])

    return buttons

def create_tool_card_text(tool: dict) -> str:
    name = tool.get("name", "Без названия")
    tool_id = tool.get("id", "Нет ID")
    obj = tool.get("object", "Не указан")
    responsible = tool.get("responsible", "Никто")
    status = "На складе" if obj.lower() == "ladu" else "На объекте"

    text = (f"*Название:* {name}\n"
            f"*ID:* {tool_id}\n"
            f"*Объект:* {obj}\n"
            f"*Ответственный:* {responsible}\n"
            f"*Статус:* {status}")
    return text

async def export_pending_to_excel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    pending = load_json(PENDING_PATH)

    if not pending:
        await query.edit_message_text("Нет данных для экспорта.")
        return

    # Преобразуем в DataFrame
    df = pd.DataFrame(pending)

    # Сохраняем во временный файл
    export_path = os.path.join(DATA_DIR, "pending_export.xlsx")
    df.to_excel(export_path, index=False)

    # Отправляем файл
    await query.message.reply_document(document=open(export_path, "rb"), filename="История_действий.xlsx")
    
    # Сообщение после отправки
    await query.edit_message_text("Файл истории успешно создан и отправлен!")

    

