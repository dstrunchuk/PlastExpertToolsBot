from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes,
    CallbackQueryHandler, MessageHandler, filters
)
import json
import os

# === КОНФИГ ===
BOT_TOKEN = "7500703930:AAFaxpYm7mcMYkosPz2Hru9uBYaMsyOD8xY"
DEVELOPER_ID = [987664835]

# === ЗАГРУЗКА / СОХРАНЕНИЕ JSON ===
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

# === МЕНЮ БРИГАДИРА ===
async def show_foreman_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📋 Мои инструменты", callback_data="my_tools")],
        [InlineKeyboardButton("🔍 Весь инструмент", callback_data="all_tools")],
        [InlineKeyboardButton("📦 Передать инструмент", callback_data="transfer_tool")],
        [InlineKeyboardButton("✅ Вернуть на склад", callback_data="return_tool")],
        [InlineKeyboardButton("➕ Добавить инструмент", callback_data="add_tool")]
    ]
    markup = InlineKeyboardMarkup(keyboard)
    if update.message:
        await update.message.reply_text("Выберите действие:", reply_markup=markup)
    else:
        await update.callback_query.message.edit_text("Выберите действие:", reply_markup=markup)

# === МЕНЮ СУПЕРВАЙЗЕРА ===
async def show_supervisor_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🔍 Весь инструмент", callback_data="all_tools")],
        [InlineKeyboardButton("◀️ Главная", callback_data="back_to_menu")]
    ]
    markup = InlineKeyboardMarkup(keyboard)
    if update.message:
        await update.message.reply_text("Меню супервайзера:", reply_markup=markup)
    else:
        await update.callback_query.message.edit_text("Меню супервайзера:", reply_markup=markup)

# === МЕНЮ РАЗРАБОТЧИКА ===
async def show_developer_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🔨 Я как бригадир", callback_data="dev_as_foreman")],
        [InlineKeyboardButton("🧠 Я как супервайзер", callback_data="dev_as_supervisor")],
        [InlineKeyboardButton("⚙️ Меню разработчика", callback_data="dev_menu")]
    ]
    markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Ты разработчик. Что хочешь делать?", reply_markup=markup)

# === /start ===
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    foremen = load_json("data/foremen.json")
    users = load_json("data/users.json")

    if user_id in DEVELOPER_ID:
        await show_developer_menu(update, context)
        return

    for f in foremen:
        if f["id"] == user_id:
            await update.message.reply_text(f"Привет, {f['name']}! Ты зарегистрирован как бригадир.")
            await show_foreman_menu(update, context)
            return

    for u in users:
        if u["id"] == user_id and u["role"] == "Супервайзер":
            await update.message.reply_text(f"Добро пожаловать, {u['name']} (Супервайзер).")
            await show_supervisor_menu(update, context)
            return

    await update.message.reply_text("Извините, вы не зарегистрированы в системе.")

# === ОБРАБОТКА КНОПОК ===
async def handle_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    action = query.data
    user_id = query.from_user.id

    if action == "dev_as_foreman":
        await show_foreman_menu(update, context)
    elif action == "dev_as_supervisor":
        await show_supervisor_menu(update, context)
    elif action == "dev_menu":
        await query.edit_message_text("Раздел разработчика — скоро.",
                                      reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Главная", callback_data="back_to_menu")]]))
    elif action == "my_tools":
        tools = load_json("data/tools.json")
        my = [t for t in tools if t.get("responsible_id") == user_id]
        msg = "Твои инструменты:\n\n" if my else "У тебя нет прикреплённых инструментов."
        for t in my:
            msg += f"• {t['name']} — {t['object']} ({t['status']})\n"
        markup = InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Главная", callback_data="back_to_menu")]])
        await query.edit_message_text(msg, reply_markup=markup)
    elif action == "all_tools":
        tools = load_json("data/tools.json")
        foremen = load_json("data/foremen.json")
        msg = "Весь инструмент:\n\n"
        for t in tools:
            f_name = t.get("responsible") or next(
            (f["name"] for f in foremen if f["id"] == t.get("responsible_id")), "не назначен"
            )
            msg += f"• {t['name']} — {t['object']} ({t['status']}), ответственный: {f_name}\n"
        markup = InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Главная", callback_data="back_to_menu")]])
        await query.edit_message_text(msg, reply_markup=markup)
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
            text=f"{tool['name']} ({tool['object']})\nПодтверди получение.",
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

# === ОБРАБОТКА СООБЩЕНИЙ ===
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
            f"{tool['name']} ({tool['object']})\nКому передаём?",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

# === ЗАПУСК ===
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start_command))
app.add_handler(CallbackQueryHandler(handle_callbacks))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

print("Бот запущен.")
app.run_polling()