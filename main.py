from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler
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

# === ПОКАЗ МЕНЮ БРИГАДИРА ===
async def show_foreman_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📋 Мои инструменты", callback_data="my_tools")],
        [InlineKeyboardButton("📦 Передать инструмент", callback_data="transfer_tool")],
        [InlineKeyboardButton("✅ Вернуть на склад", callback_data="return_tool")],
        [InlineKeyboardButton("➕ Добавить инструмент", callback_data="add_tool")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message:
        await update.message.reply_text("Выберите действие:", reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.message.edit_text("Выберите действие:", reply_markup=reply_markup)

# === ПОКАЗ МЕНЮ РАЗРАБОТЧИКА ===
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
            return

    await update.message.reply_text("Извините, вы не зарегистрированы в системе.")

# === ОБРАБОТКА ВСЕХ КНОПОК ===
async def handle_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    action = query.data
    user_id = query.from_user.id

    if action == "dev_as_foreman":
        await show_foreman_menu(update, context)

    elif action == "dev_as_supervisor":
        await query.edit_message_text("Здесь будет меню супервайзера (в разработке).")

    elif action == "dev_menu":
        await query.edit_message_text("Раздел разработчика: скоро здесь будут кнопки для выгрузки, дампа и лога.")

    elif action == "my_tools":
        tools = load_json("data/tools.json")
        user_tools = [t for t in tools if t.get("responsible_id") == user_id]
        if not user_tools:
            await query.edit_message_text("У тебя пока нет прикреплённых инструментов.")
        else:
            msg = "Твои инструменты:\n\n"
            for tool in user_tools:
                msg += f"• {tool.get('name')} — {tool.get('object')} ({tool.get('status')})\n"
            await query.edit_message_text(msg)

    elif action == "transfer_tool":
        await query.edit_message_text("Сканируй QR-код инструмента для передачи.")
    elif action == "return_tool":
        await query.edit_message_text("Сканируй QR-код, чтобы вернуть инструмент на склад.")
    elif action == "add_tool":
        await query.edit_message_text("Введи данные нового инструмента.")
    else:
        await query.edit_message_text("Неизвестное действие.")

# === ЗАПУСК ===
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start_command))
app.add_handler(CallbackQueryHandler(handle_callbacks))

print("Бот запущен.")
app.run_polling()