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

# === ЗАГРУЗКА JSON ===
def load_json(path):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# === СОХРАНЕНИЕ JSON ===
def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
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
    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.message:
        await update.message.reply_text("Выберите действие:", reply_markup=reply_markup)
    else:
        await update.callback_query.message.edit_text("Выберите действие:", reply_markup=reply_markup)

# === МЕНЮ СУПЕРВАЙЗЕРА ===
async def show_supervisor_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🔍 Весь инструмент", callback_data="all_tools")],
        [InlineKeyboardButton("◀️ Назад", callback_data="back_to_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Меню супервайзера:", reply_markup=reply_markup)

# === МЕНЮ РАЗРАБОТЧИКА ===
async def show_developer_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🔨 Я как бригадир", callback_data="dev_as_foreman")],
        [InlineKeyboardButton("🧠 Я как супервайзер", callback_data="dev_as_supervisor")],
        [InlineKeyboardButton("⚙️ Меню разработчика", callback_data="dev_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Ты разработчик. Что хочешь делать?", reply_markup=reply_markup)

# === /start ===
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    foremen = load_json("data/foremen.json")
    users = load_json("data/users.json")

    if user_id in DEVELOPER_ID:
        await show_developer_menu(update, context)
        return

    for foreman in foremen:
        if foreman["id"] == user_id:
            await update.message.reply_text(f"Привет, {foreman['name']}! Ты зарегистрирован как бригадир.")
            await show_foreman_menu(update, context)
            return

    for user in users:
        if user["id"] == user_id and user["role"] == "Супервайзер":
            await update.message.reply_text(f"Добро пожаловать, {user['name']} (Супервайзер).")
            await show_supervisor_menu(update, context)
            return

    await update.message.reply_text("Извините, вы не зарегистрированы в системе.")

# === КНОПКИ ===
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
        await query.edit_message_text("Раздел разработчика: скоро будет доступ к логам и выгрузке.")
    elif action == "my_tools":
        tools = load_json("data/tools.json")
        my = [t for t in tools if t.get("responsible_id") == user_id]
        msg = "Твои инструменты:\n\n" if my else "У тебя нет прикреплённых инструментов."
        for t in my:
            msg += f"• {t['name']} — {t['object']} ({t['status']})\n"
        await query.edit_message_text(msg)
    elif action == "all_tools":
        tools = load_json("data/tools.json")
        foremen = load_json("data/foremen.json")
        msg = "Весь инструмент:\n\n"
        for t in tools:
            f_name = next((f["name"] for f in foremen if f["id"] == t["responsible_id"]), "неизвестен")
            msg += f"• {t['name']} — {t['object']} ({t['status']}), ответственный: {f_name}\n"
        await query.edit_message_text(msg + "\n◀️ /start — назад")
    elif action == "transfer_tool":
        await query.edit_message_text("Отправь ID (или отсканируй QR) инструмента.")
        context.user_data["transfer_stage"] = "waiting_for_tool_id"
    elif action.startswith("give_to_"):
        receiver_id = int(action.split("_")[-1])
        tool = context.user_data.get("transfer_tool")
        context.user_data["pending_transfer"] = {
            "tool_id": tool["id"],
            "from_id": query.from_user.id,
            "to_id": receiver_id
        }
        await context.bot.send_message(
            chat_id=receiver_id,
            text=f"{tool['name']} ({tool['object']})\nПодтверди получение.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Принять", callback_data=f"confirm_{tool['id']}")],
                [InlineKeyboardButton("❌ Отказаться", callback_data="cancel_transfer")]
            ])
        )
        await query.edit_message_text("Запрос отправлен. Ожидаем подтверждения.")
    elif action.startswith("confirm_"):
        tool_id = action.split("_")[1]
        transfer = context.user_data.get("pending_transfer")
        if transfer and transfer["tool_id"] == tool_id:
            tools = load_json("data/tools.json")
            for t in tools:
                if t["id"] == tool_id:
                    t["responsible_id"] = query.from_user.id
            save_json("data/tools.json", tools)
            await query.edit_message_text("Инструмент принят.")
            await context.bot.send_message(transfer["from_id"], "Инструмент успешно передан.")
            context.user_data.clear()
    elif action == "cancel_transfer":
        await query.edit_message_text("Передача отменена.")
    elif action == "back_to_menu":
        await show_foreman_menu(update, context)
    elif action == "return_tool":
        await query.edit_message_text("Сканируй QR-код для возврата.")
    elif action == "add_tool":
        await query.edit_message_text("Введи данные нового инструмента.")
    else:
        await query.edit_message_text("Неизвестное действие.")

# === СООБЩЕНИЯ ===
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()
    tools = load_json("data/tools.json")
    foremen = load_json("data/foremen.json")

    if context.user_data.get("transfer_stage") == "waiting_for_tool_id":
        tool = next((t for t in tools if t["id"] == text), None)
        if not tool:
            await update.message.reply_text("Инструмент не найден.")
            return
        if tool["responsible_id"] != user_id:
            await update.message.reply_text("Ты не являешься ответственным за этот инструмент.")
            return
        context.user_data["transfer_tool"] = tool
        context.user_data["transfer_stage"] = "select_receiver"
        buttons = [[InlineKeyboardButton(f["name"], callback_data=f"give_to_{f['id']}")]
                   for f in foremen if f["id"] != user_id]
        buttons.append([InlineKeyboardButton("◀️ Назад", callback_data="back_to_menu")])
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