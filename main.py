from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes,
    CallbackQueryHandler, MessageHandler, filters
)
import json
import os

BOT_TOKEN = "7500703930:AAEvPawqHdW5hqohCxJrZekn3Mp8BBB1j6U"
ITEMS_PER_PAGE = 10

def load_json(path):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_pending():
    if not os.path.exists("data/pending.json"):
        return {}
    with open("data/pending.json", "r", encoding="utf-8") as f:
        return json.load(f)

def save_pending(data):
    with open("data/pending.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

async def show_foreman_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📋 Мои инструменты", callback_data="my_tools")],
        [InlineKeyboardButton("🔍 Весь инструмент", callback_data="all_tools_0")],
        [InlineKeyboardButton("🔎 Найти инструмент", callback_data="search_tool")],
        [InlineKeyboardButton("🆔 Найти по ID", callback_data="search_by_id")],
        [InlineKeyboardButton("📦 Передать инструмент", callback_data="transfer_tool")],
        [InlineKeyboardButton("✅ Вернуть на склад", callback_data="return_tool")],
        [InlineKeyboardButton("➕ Добавить инструмент", callback_data="add_tool")]
    ]
    markup = InlineKeyboardMarkup(keyboard)
    if update.message:
        await update.message.reply_text("Выберите действие:", reply_markup=markup)
    elif update.callback_query:
        await update.callback_query.message.edit_text("Выберите действие:", reply_markup=markup)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Добро пожаловать в Plast Expert Tools!")
    user_id = update.effective_user.id
    foremen = load_json("data/foremen.json")
    users = load_json("data/users.json")

    for f in foremen:
        if f["id"] == user_id:
            await update.message.reply_text(f"Привет, {f['name']}! Ты зарегистрирован как бригадир.")
            await show_foreman_menu(update, context)
            return

    for u in users:
        if u["id"] == user_id and u["role"] == "Супервайзер":
            await update.message.reply_text(f"Добро пожаловать, {u['name']} (Супервайзер).")
            return

    await update.message.reply_text("Извините, вы не зарегистрированы в системе.")

async def show_page_of_tools(update: Update, context: ContextTypes.DEFAULT_TYPE, page: int):
    tools = load_json("data/tools.json")
    foremen = load_json("data/foremen.json")

    start = page * ITEMS_PER_PAGE
    end = start + ITEMS_PER_PAGE
    total_pages = (len(tools) - 1) // ITEMS_PER_PAGE + 1
    current_tools = tools[start:end]

    msg = f"Весь инструмент (стр. {page+1}/{total_pages}):"
    for t in current_tools:
        f_name = t.get("responsible") or next((f["name"] for f in foremen if f["id"] == t.get("responsible_id")), "не назначен")
        msg += f"• {t['name']} — {t['object']} ({t['status']}), ответственный: {f_name}"

    buttons = []
    if page > 0:
        buttons.append(InlineKeyboardButton("⬅️ Назад", callback_data=f"all_tools_{page-1}"))
    if end < len(tools):
        buttons.append(InlineKeyboardButton("➡️ Далее", callback_data=f"all_tools_{page+1}"))
    buttons.append(InlineKeyboardButton("◀️ Главная", callback_data="back_to_menu"))
    markup = InlineKeyboardMarkup([buttons])
    await update.callback_query.message.edit_text(msg, reply_markup=markup)

async def handle_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    action = query.data
    user_id = query.from_user.id

    if action == "my_tools":
        tools = load_json("data/tools.json")
        my = [t for t in tools if t.get("responsible_id") == user_id]
        msg = "Твои инструменты:" if my else "У тебя нет прикреплённых инструментов."
        for t in my:
            msg += f"• {t['name']} — {t['object']} ({t['status']})"
        markup = InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Главная", callback_data="back_to_menu")]])
        await query.edit_message_text(msg, reply_markup=markup)

    elif action.startswith("all_tools_"):
        page = int(action.split("_")[-1])
        await show_page_of_tools(update, context, page)

    elif action == "search_tool":
        await query.edit_message_text("Введи название или часть названия инструмента для поиска:",
                                      reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Главная", callback_data="back_to_menu")]]))
        context.user_data["awaiting_search"] = True

    elif action == "search_by_id":
        await query.edit_message_text("Введи ID инструмента (например: 23.12):",
                                      reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Главная", callback_data="back_to_menu")]]))
        context.user_data["awaiting_id_search"] = True

    elif action == "transfer_tool":
        await query.edit_message_text("Отправь ID инструмента, который хочешь передать.",
                                      reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Главная", callback_data="back_to_menu")]]))
        context.user_data["transfer_stage"] = "waiting_for_tool_id"

    elif action.startswith("give_to_"):
        receiver_id = int(action.split("_")[-1])
        tool = context.user_data.get("transfer_tool")
        tool_id = str(tool["id"])
        pending = load_pending()
        pending[tool_id] = {
            "tool_id": tool_id,
            "from_id": user_id,
            "to_id": receiver_id
        }
        save_pending(pending)
        await context.bot.send_message(
            chat_id=receiver_id,
            text=f"{tool['name']} ({tool['object']})Подтверди получение.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Принять", callback_data=f"confirm_{tool_id}")],
                [InlineKeyboardButton("❌ Отказаться", callback_data="cancel_transfer")]
            ])
        )
        await query.edit_message_text("Запрос отправлен. Ожидаем подтверждения.",
                                      reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Главная", callback_data="back_to_menu")]]))

    elif action.startswith("confirm_"):
        tool_id = action.split("_")[1]
        pending = load_pending()
        transfer = pending.get(tool_id)
        if not transfer:
            await query.edit_message_text("Передача не найдена или уже подтверждена.",
                                          reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Главная", callback_data="back_to_menu")]]))
            return
        tools = load_json("data/tools.json")
        for t in tools:
            if str(t["id"]) == tool_id:
                t["responsible_id"] = user_id
        save_json("data/tools.json", tools)
        del pending[tool_id]
        save_pending(pending)
        await query.edit_message_text("Инструмент успешно принят.",
                                      reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Главная", callback_data="back_to_menu")]]))
        await context.bot.send_message(transfer["from_id"], "Инструмент передан и принят.")

    elif action == "cancel_transfer":
        await query.edit_message_text("Передача отменена.",
                                      reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Главная", callback_data="back_to_menu")]]))

    elif action == "return_tool":
        await query.edit_message_text("Сканируй QR-код для возврата.",
                                      reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Главная", callback_data="back_to_menu")]]))

    elif action == "add_tool":
        await query.edit_message_text("Введи данные нового инструмента.",
                                      reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Главная", callback_data="back_to_menu")]]))

    elif action == "back_to_menu":
        await show_foreman_menu(update, context)

    else:
        await query.edit_message_text("Неизвестное действие.",
                                      reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Главная", callback_data="back_to_menu")]]))

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()
    tools = load_json("data/tools.json")
    foremen = load_json("data/foremen.json")

    if context.user_data.get("transfer_stage") == "waiting_for_tool_id":
        tool = next((t for t in tools if str(t["id"]) == text), None)
        if not tool:
            await update.message.reply_text("Инструмент не найден.")
            return
        if tool["responsible_id"] != user_id:
            await update.message.reply_text("Этот инструмент не принадлежит тебе.")
            return
        context.user_data["transfer_tool"] = tool
        context.user_data["transfer_stage"] = "select_receiver"
        buttons = [[InlineKeyboardButton(f["name"], callback_data=f"give_to_{f['id']}")]
                   for f in foremen if f["id"] != user_id]
        buttons.append([InlineKeyboardButton("◀️ Главная", callback_data="back_to_menu")])
        await update.message.reply_text(
            f"{tool['name']} ({tool['object']})Кому передаём?",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    if context.user_data.get("awaiting_search"):
        context.user_data["awaiting_search"] = False
        matches = [t for t in tools if text.lower() in t["name"].lower()]
        if not matches:
            await update.message.reply_text("Ничего не найдено.",
                                            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Главная", callback_data="back_to_menu")]]))
            return
        msg = "Найдено:"
        for t in matches:
            responsible = t.get("responsible") or next((f["name"] for f in foremen if f["id"] == t.get("responsible_id")), "не назначен")
            msg += f"• {t['name']} — {t['object']} ({t['status']}), ответственный: {responsible}"
        await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Главная", callback_data="back_to_menu")]]))
        return

    if context.user_data.get("awaiting_id_search"):
        context.user_data["awaiting_id_search"] = False
        tool = next((t for t in tools if str(t["id"]) == text), None)
        if not tool:
            await update.message.reply_text("Инструмент с таким ID не найден.",
                                            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Главная", callback_data="back_to_menu")]]))
            return
        responsible = tool.get("responsible") or next((f["name"] for f in foremen if f["id"] == tool.get("responsible_id")), "не назначен")
        msg = f"• {tool['name']} — {tool['object']}Статус: {tool['status']}Ответственный: {responsible}"
        await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Главная", callback_data="back_to_menu")]]))
        return

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start_command))
app.add_handler(CallbackQueryHandler(handle_callbacks))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

print("Бот запущен.")
app.run_polling()