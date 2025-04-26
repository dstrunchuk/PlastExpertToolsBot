from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import ContextTypes
import os, json
import pandas as pd
from io import BytesIO
from datetime import datetime
from handlers.database import get_tool_by_id, update_tool, log_action, get_all_foremen, get_all_users, get_all_tools, get_tool_history, get_user_by_id
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

    user = await get_user_by_id(user_id)
    if not user:
        await query.edit_message_text("Пользователь не найден.", reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("◀️ Главное меню", callback_data="main_back")]
        ]))
        return

    data = query.data
    parts = data.split(":")
    action = parts[0]
    tool_id = parts[1]

    tool = await get_tool_by_id(tool_id)
    if not tool:
        await query.edit_message_text("Инструмент не найден.", reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("◀️ Главное меню", callback_data="main_back")]
        ]))
        return

    if action == "take":
        tool["responsible"] = user["name"]
        tool["responsible_id"] = user_id
        await update_tool(tool)
        await log_action({
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "action": "Стал ответственным",
            "tool_id": tool["id"],
            "tool_name": tool["name"],
            "object": tool["object"],
            "responsible": user["name"]
        })
        await query.edit_message_text(f"Вы стали ответственным за {tool['name']}.", reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("◀️ Главное меню", callback_data="main_back")]
        ]))

    elif action == "store":
        tool["responsible"] = None
        tool["responsible_id"] = None
        tool["object"] = "Ladu"
        await update_tool(tool)
        await log_action({
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "action": "Оставил на складе",
            "tool_id": tool["id"],
            "tool_name": tool["name"],
            "object": tool["object"],
            "responsible": "Никто"
        })
        await query.edit_message_text(f"Инструмент {tool['name']} оставлен на складе.", reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("◀️ Главное меню", callback_data="main_back")]
        ]))

    elif action == "request":
        responsible_id = tool.get("responsible_id")
        if responsible_id:
            responsible_user = await get_user_by_id(responsible_id)
            if responsible_user:
                try:
                    await context.bot.send_message(
                        chat_id=responsible_id,
                        text=f"🔔 Пользователь {user['name']} запрашивает инструмент: {tool['name']} (ID: {tool.get('id', 'нет ID')})"
                    )
                    await query.edit_message_text(f"Запрос отправлен {responsible_user['name']}.", reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("◀️ Главное меню", callback_data="main_back")]
                    ]))
                except Exception as e:
                    print(f"Ошибка отправки запроса: {e}")
                    await query.edit_message_text("Не удалось отправить запрос.", reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("◀️ Главное меню", callback_data="main_back")]
                    ]))
            else:
                await query.edit_message_text("Ответственный пользователь не найден.", reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("◀️ Главное меню", callback_data="main_back")]
                ]))
        else:
            await query.edit_message_text("У инструмента нет ответственного.", reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("◀️ Главное меню", callback_data="main_back")]
            ]))

    elif action == "transfer":
        foremen = await get_all_foremen()
        buttons = []
        seen = set()
        for person in foremen:
            if person["name"] not in seen:
                buttons.append([InlineKeyboardButton(person["name"], callback_data=f"confirm_transfer:{tool_id}:{person['id']}")])
                seen.add(person["name"])
        buttons.append([InlineKeyboardButton("◀️ Главное меню", callback_data="main_back")])
        await query.edit_message_text("Кому передать инструмент?", reply_markup=InlineKeyboardMarkup(buttons))

    elif action == "assign":
        foremen = await get_all_foremen()
        buttons = []
        seen = set()
        for person in foremen:
            if person["name"] not in seen:
                buttons.append([InlineKeyboardButton(person["name"], callback_data=f"confirm_assign:{tool_id}:{person['id']}")])
                seen.add(person["name"])
        buttons.append([InlineKeyboardButton("◀️ Главное меню", callback_data="main_back")])
        await query.edit_message_text("Кого назначить ответственным?", reply_markup=InlineKeyboardMarkup(buttons))

    elif action == "confirm_transfer":
        _, tool_id, target_id = parts
        new_user = await get_user_by_id(int(target_id))
        if new_user:
            tool["responsible"] = new_user["name"]
            tool["responsible_id"] = new_user["id"]
            await update_tool(tool)
            await log_action({
                "timestamp": datetime.now().isoformat(),
                "user_id": user_id,
                "action": f"Передал инструмент → {new_user['name']}",
                "tool_id": tool["id"],
                "tool_name": tool["name"],
                "object": tool["object"],
                "responsible": new_user["name"]
            })
            await query.edit_message_text(f"Инструмент {tool['name']} передан {new_user['name']}.", reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("◀️ Главное меню", callback_data="main_back")]
            ]))
        else:
            await query.edit_message_text("Не удалось передать инструмент.", reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("◀️ Главное меню", callback_data="main_back")]
            ]))

    elif action == "confirm_assign":
        _, tool_id, target_id = parts
        new_user = await get_user_by_id(int(target_id))
        if new_user:
            tool["responsible"] = new_user["name"]
            tool["responsible_id"] = new_user["id"]
            await update_tool(tool)
            await log_action({
                "timestamp": datetime.now().isoformat(),
                "user_id": user_id,
                "action": f"Назначил {new_user['name']} ответственным",
                "tool_id": tool["id"],
                "tool_name": tool["name"],
                "object": tool["object"],
                "responsible": new_user["name"]
            })
            await query.edit_message_text(f"{new_user['name']} назначен ответственным за {tool['name']}.", reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("◀️ Главное меню", callback_data="main_back")]
            ]))
        else:
            await query.edit_message_text("Не удалось назначить.", reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("◀️ Главное меню", callback_data="main_back")]
            ]))

    else:
        await query.edit_message_text("Неизвестное действие.", reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("◀️ Главное меню", callback_data="main_back")]
        ]))

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

    # Если было сообщение "Введи ID или название инструмента" — удаляем его
    find_prompt_id = context.user_data.pop("find_prompt_message_id", None)
    if find_prompt_id:
        try:
            await update.effective_chat.delete_message(find_prompt_id)
        except Exception as e:
            print(f"Не удалось удалить сообщение поиска: {e}")

    # Ищем сначала по ID
    for tool in tools:
        if str(tool.get("id")) == user_message:
            found_tools = [tool]
            break

    # Потом по названию (если по ID не нашли)
    if not found_tools:
        for tool in tools:
            if tool.get("name") and user_message.lower() in tool["name"].lower():
                found_tools.append(tool)

    # Удаляем сообщение поиска
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

    # Если найден один инструмент
    if len(found_tools) == 1:
        tool = found_tools[0]

        text = (
            f"Название: {tool.get('name', 'Без названия')}\n"
            f"ID: {tool.get('id', 'Нет ID')}\n"
            f"Объект: {tool.get('object', 'Не указан')}\n"
            f"Ответственный: {tool.get('responsible', 'Никто')}"
        )

        buttons = generate_action_buttons(tool, role)
        buttons.insert(0, [InlineKeyboardButton("🗂 История", callback_data=f"export_one:{tool.get('id')}")])

        await update.effective_chat.send_message(
            text=text,
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        return

    # Если найдено несколько инструментов
    context.user_data["found_tools"] = found_tools
    context.user_data["search_page"] = 0

    await send_search_results(update, context)

async def send_search_results(update: Update, context: ContextTypes.DEFAULT_TYPE):
    found_tools = context.user_data.get("found_tools", [])
    page = context.user_data.get("search_page", 0)

    tools_per_page = 5
    start = page * tools_per_page
    end = start + tools_per_page
    current_tools = found_tools[start:end]

    if not current_tools:
        await update.effective_chat.send_message(
            "Инструменты не найдены на этой странице.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("◀️ Главное меню", callback_data="main_back")]
            ])
        )
        return

    message = "Найдено несколько инструментов:\n\n"
    keyboard = []
    for idx, tool in enumerate(current_tools, start=start+1):
        message += f"{idx}. {tool.get('name', 'Без названия')} (ID: {tool.get('id', 'Нет ID')})\n"
        keyboard.append([
            InlineKeyboardButton(f"{tool.get('name', 'Без названия')}", callback_data=f"view_tool:{tool.get('id')}")
        ])

    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("◀️ Назад", callback_data="search_prev"))
    if end < len(found_tools):
        nav_buttons.append(InlineKeyboardButton("Вперёд ▶️", callback_data="search_next"))

    nav_buttons.append(InlineKeyboardButton("◀️ Главное меню", callback_data="main_back"))
    keyboard.append(nav_buttons)

    await update.effective_chat.send_message(
        text=message.strip(),
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    async def search_next(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.callback_query.answer()
        context.user_data["search_page"] += 1
        await update.callback_query.delete_message()
        await send_search_results(update, context)

    async def search_prev(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.callback_query.answer()
        context.user_data["search_page"] -= 1
        await update.callback_query.delete_message()
        await send_search_results(update, context)
        
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

    if role in ["Ответственный", "Админ"]:
        if not responsible_id:
            buttons.append([InlineKeyboardButton("✅ Стать ответственным", callback_data=f"take:{tool['id']}")])
        elif responsible_id and responsible_id == tool.get("responsible_id"):
            buttons.append([InlineKeyboardButton("📤 Передать", callback_data=f"transfer:{tool['id']}")])
            buttons.append([InlineKeyboardButton("🏬 Оставить на складе", callback_data=f"store:{tool['id']}")])
        else:
            buttons.append([InlineKeyboardButton("📥 Запросить передачу", callback_data=f"request:{tool['id']}")])

    if role in ["Супервайзер", "Босс"]:
        buttons.append([InlineKeyboardButton("👤 Назначить ответственного", callback_data=f"assign:{tool['id']}")])
        buttons.append([InlineKeyboardButton("🏬 Оставить на складе", callback_data=f"store:{tool['id']}")])

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

async def export_one_tool_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    tool_id = query.data.split(":")[1]
    history = await get_tool_history(tool_id)

    if not history:
        await query.edit_message_text(
            "Нет действий с этим инструментом.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("◀️ Главное меню", callback_data="main_back")]
            ])
        )
        return

    # Генерируем Excel файл
    df = pd.DataFrame(history)
    file_path = f"/tmp/history_{tool_id}.xlsx"
    df.to_excel(file_path, index=False)

    # Отправляем файл пользователю
    await query.message.reply_document(
        document=open(file_path, "rb"),
        filename=f"History_{tool_id}.xlsx",
        caption="История инструмента."
    )

    # Удаляем файл после отправки
    os.remove(file_path)

    # После отправки файла отправляем кнопку на главное меню
    await query.message.reply_text(
        "Выберите действие:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("◀️ Главное меню", callback_data="main_back")]
        ])
    )   

