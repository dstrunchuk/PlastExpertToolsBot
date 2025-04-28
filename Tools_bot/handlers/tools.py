from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import ContextTypes
import pandas as pd
from datetime import datetime
from handlers.database import get_tool_by_id, update_tool, log_action, get_all_foremen, get_all_users, get_all_tools, get_tool_history, get_user_by_id
import re


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
        await log_action(user_id, "Стал ответственным", tool)
        await query.edit_message_text(f"Вы стали ответственным за {tool['name']}.", reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("◀️ Главное меню", callback_data="main_back")]
        ]))

    elif action == "store":
        tool["responsible"] = None
        tool["responsible_id"] = None
        tool["object"] = "Ladu"
        await update_tool(tool)
        await log_action(user_id, "Оставил на складе", tool)
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
            if person["name"] not in seen and person["role"] != "Супервайзер":
                buttons.append([InlineKeyboardButton(person["name"], callback_data=f"confirm_transfer:{tool_id}:{person['id']}")])
                seen.add(person["name"])
        buttons.append([InlineKeyboardButton("◀️ Главное меню", callback_data="main_back")])
        await query.edit_message_text("Кому передать инструмент?", reply_markup=InlineKeyboardMarkup(buttons))

    elif action == "start_transfer":
        _, tool_id, target_id = parts
        target_id = int(target_id)

        try:
            await context.bot.send_message(
                chat_id=target_id,
                text=f"🔔 Вам хотят передать инструмент: {tool['name']} (ID: {tool.get('id')}). Нажмите ниже, чтобы принять.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("✅ Принять инструмент", callback_data=f"confirm_accept:{tool_id}:{user_id}")]
                ])
            )
            await query.edit_message_text("Запрос на передачу отправлен. Ждем подтверждения.")

        # Сохраняем в память pending_transfer
            context.bot_data.setdefault("pending_transfers", {})[tool_id] = {
                "from_user_id": user_id,
                "to_user_id": target_id,
                "timestamp": datetime.now().isoformat()
            }

        # Планируем напоминание через 1 час
            await context.job_queue.run_once(
                schedule_transfer_reminder,
                when=3600,
                data={
                    "to_user_id": target_id,
                    "tool_name": tool["name"],
                    "tool_id": tool["id"]
                }
            )

        except Exception as e:
            print(f"Ошибка при отправке передачи: {e}")
            await query.edit_message_text("Не удалось отправить запрос на передачу.")

    elif action == "assign":
        foremen = await get_all_foremen()
        buttons = []
        seen = set()
        for person in foremen:
            if person["name"] not in seen and person["role"] != "Супервайзер":
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
            await log_action(user_id, f"Передал инструмент → {new_user['name']}", tool)
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
            await log_action(user_id, f"Назначил {new_user['name']} ответственным", tool)
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

async def confirm_accept_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    parts = query.data.split(":")
    tool_id = parts[1]
    from_user_id = int(parts[2])
    accepting_user_id = query.from_user.id

    pending_transfers = context.bot_data.get("pending_transfers", {})

    transfer_info = pending_transfers.get(tool_id)
    if not transfer_info:
        await query.edit_message_text("Передача не найдена или уже подтверждена.")
        return

    if transfer_info["to_user_id"] != accepting_user_id:
        await query.edit_message_text("Вы не можете принять эту передачу.")
        return

    # Обновляем владельца
    tool = await get_tool_by_id(tool_id)
    if tool:
        new_user = await get_user_by_id(accepting_user_id)
        tool["responsible"] = new_user["name"]
        tool["responsible_id"] = new_user["id"]
        await update_tool(tool)
        await log_action(accepting_user_id, "Принял инструмент", tool)

        # Удаляем из pending
        del pending_transfers[tool_id]

        await query.edit_message_text(f"Вы успешно приняли инструмент: {tool['name']}.")
    else:
        await query.edit_message_text("Инструмент не найден.")

async def schedule_transfer_reminder(context: ContextTypes.DEFAULT_TYPE):
    job_data = context.job.data
    to_user_id = job_data["to_user_id"]
    tool_name = job_data["tool_name"]
    tool_id = job_data["tool_id"]

    try:
        await context.bot.send_message(
            chat_id=to_user_id,
            text=f"⏰ Напоминание: Вы не подтвердили приём инструмента: {tool_name} (ID: {tool_id}). Пожалуйста, подтвердите!"
        )
    except Exception as e:
        print(f"Ошибка при отправке напоминания: {e}")

async def update_tool_card(query, tool: dict, user_id: int):
    users = await get_all_users()
    user = next((u for u in users if u["id"] == user_id), None)
    role = user.get("role", "Ответственный") if user else "Ответственный"

    text = create_tool_card_text(tool)
    buttons = generate_action_buttons(tool, role, user_id)
    reply_markup = InlineKeyboardMarkup(buttons) if buttons else None

    await query.edit_message_text(text=text, parse_mode="Markdown", reply_markup=reply_markup)

async def process_tool_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    user_id = update.effective_user.id
    user = await get_user_by_id( user_id)
    role = user.get("role", "Ответственный") if user else "Ответственный"

    user_message = update.message.text.strip()
    tools = await get_all_tools()

    # Удаляем сообщение "Введи ID или название инструмента"
    find_prompt_id = context.user_data.pop("find_prompt_message_id", None)
    if find_prompt_id:
        try:
            await update.effective_chat.delete_message(find_prompt_id)
        except Exception as e:
            print(f"Не удалось удалить find_prompt сообщение: {e}")

    # Удаляем сообщение пользователя
    try:
        await update.message.delete()
    except:
        pass

    # Ищем по ID
    exact_tool = next((tool for tool in tools if str(tool.get("id")) == user_message), None)

    if exact_tool:
        text = (
            f"Название: {exact_tool.get('name', 'Без названия')}\n"
            f"ID: {exact_tool.get('id', 'Нет ID')}\n"
            f"Объект: {exact_tool.get('object', 'Не указан')}\n"
            f"Ответственный: {exact_tool.get('responsible', 'Никто')}"
        )

        # генерируем только действия без добавления кнопки "Главное меню"
        buttons = generate_action_buttons(exact_tool, role, user_id)

        # Добавляем "История"
        buttons.insert(0, [InlineKeyboardButton("🗂 История", callback_data=f"export_one:{exact_tool.get('id')}")])

    

        await update.effective_chat.send_message(
            text=text,
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        return

    # Поиск по имени
    found_tools = [tool for tool in tools if tool.get("name") and user_message.lower() in tool["name"].lower()]

    if not found_tools:
        await update.effective_chat.send_message(
            "Инструмент не найден.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("◀️ Главное меню", callback_data="main_back")]
            ])
        )
        return

    # Если найдено несколько
    context.user_data["found_tools"] = found_tools
    context.user_data["search_page"] = 0
    await send_search_results(update, context)


async def send_search_results(update: Update, context: ContextTypes.DEFAULT_TYPE):
    found_tools = context.user_data.get("found_tools", [])
    page = context.user_data.get("search_page", 0)

    if not found_tools:
        await update.effective_chat.send_message(
            "Инструменты не найдены.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("◀️ Главное меню", callback_data="main_back")]
            ])
        )
        return

    tools_per_page = 5
    start = page * tools_per_page
    end = start + tools_per_page
    current_tools = found_tools[start:end]

    if not current_tools:
        await update.effective_chat.send_message(
            "На этой странице нет инструментов.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("◀️ Главное меню", callback_data="main_back")]
            ])
        )
        return

    message = "Найденные инструменты:\n\n"
    for idx, tool in enumerate(current_tools, start=start+1):
        name = tool.get('name', 'Без названия')
        tool_id = tool.get('id', 'Нет ID')
        responsible = tool.get('responsible', 'Никто')
        message += f"{idx}. {name} (ID: {tool_id}) — Ответственный: {responsible}\n"

    navigation_buttons = []
    if start > 0:
        navigation_buttons.append(InlineKeyboardButton("◀️ Назад", callback_data="search_prev"))
    if end < len(found_tools):
        navigation_buttons.append(InlineKeyboardButton("Вперёд ▶️", callback_data="search_next"))

    buttons = []
    if navigation_buttons:
        buttons.append(navigation_buttons)
    buttons.append([InlineKeyboardButton("◀️ Главное меню", callback_data="main_back")])

    # Вот здесь различие:
    if update.callback_query:
        await update.callback_query.edit_message_text(
            text=message.strip(),
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    else:
        await update.effective_chat.send_message(
            text=message.strip(),
            reply_markup=InlineKeyboardMarkup(buttons)
        )

async def search_next(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["search_page"] += 1
    await send_search_results(update, context)

async def search_prev(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["search_page"] -= 1
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

    tools = await get_all_tools()
    tool_id = query.data.split(":")[1]
    tool = next((t for t in tools if str(t.get("id")) == tool_id), None)

    if not tool:
        await query.edit_message_text("Инструмент не найден.")
        return

    user_id = query.from_user.id
    users = await get_all_users()
    user = next((u for u in users if u["id"] == user_id), None)
    role = user.get("role", "Ответственный") if user else "Ответственный"

    text = create_tool_card_text(tool)
    buttons = generate_action_buttons(tool, role, user_id)
    reply_markup = InlineKeyboardMarkup(buttons) if buttons else None

    await query.edit_message_text(text=text, parse_mode="Markdown", reply_markup=reply_markup)

async def handle_view_tool_by_index(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    users = await get_all_users()
    tools = await get_all_tools()

    try:
        index = int(query.data.split(":")[1])
        tool = tools[index]
    except (IndexError, ValueError):
        await query.edit_message_text("Инструмент не найден.")
        return

    user = next((u for u in users if u["id"] == user_id), None)
    role = user.get("role", "Ответственный") if user else "Ответственный"

    text = create_tool_card_text(tool)
    buttons = generate_action_buttons(tool, role, user_id)
    reply_markup = InlineKeyboardMarkup(buttons) if buttons else None

    await query.edit_message_text(text=text, parse_mode="Markdown", reply_markup=reply_markup)

def generate_action_buttons(tool: dict, role: str, user_id: int):
    buttons = []
    responsible_id = tool.get("responsible_id")

    if role in ["Ответственный", "Админ"]:
        if not responsible_id:
            buttons.append([InlineKeyboardButton("✅ Стать ответственным", callback_data=f"take:{tool['id']}")])
        elif responsible_id == user_id:
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

