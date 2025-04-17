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
        await query.edit_message_text("Отправь мне ID (или отсканируй QR) инструмента, который хочешь передать.")
        context.user_data["transfer_stage"] = "waiting_for_tool_id"

    elif action.startswith("give_to_"):
        receiver_id = int(action.split("_")[-1])
        tool = context.user_data.get("transfer_tool")
        if not tool:
            await query.edit_message_text("Ошибка: инструмент не найден в контексте.")
            return

        sender_id = query.from_user.id
        context.user_data["pending_transfer"] = {
            "tool_id": tool["id"],
            "from_id": sender_id,
            "to_id": receiver_id
        }

        await context.bot.send_message(
            chat_id=receiver_id,
            text=f"Бригадир хочет передать тебе инструмент:\n\n"
                 f"{tool['name']} — {tool['object']}\n"
                 f"Подтверди получение.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Принять", callback_data=f"confirm_{tool['id']}")],
                [InlineKeyboardButton("❌ Отказаться", callback_data="cancel_transfer")]
            ])
        )

        await query.edit_message_text("Запрос отправлен. Ожидаем подтверждения.")

    elif action.startswith("confirm_"):
        tool_id = action.split("_")[1]
        transfer = context.user_data.get("pending_transfer")

        if not transfer or transfer["tool_id"] != tool_id:
            await query.edit_message_text("Ошибка: нет активной передачи.")
            return

        tools = load_json("data/tools.json")
        tool = next((t for t in tools if t["id"] == tool_id), None)
        if not tool:
            await query.edit_message_text("Инструмент не найден.")
            return

        tool["responsible_id"] = query.from_user.id
        with open("data/tools.json", "w", encoding="utf-8") as f:
            json.dump(tools, f, ensure_ascii=False, indent=2)

        await query.edit_message_text("Ты принял инструмент. Теперь он закреплён за тобой.")

        await context.bot.send_message(
            chat_id=transfer["from_id"],
            text="Инструмент успешно передан и принят другим бригадиром."
        )

        context.user_data.clear()

    elif action == "cancel_transfer":
        await query.edit_message_text("Передача отменена.")

    elif action == "return_tool":
        await query.edit_message_text("Сканируй QR-код, чтобы вернуть инструмент на склад.")

    elif action == "add_tool":
        await query.edit_message_text("Введи данные нового инструмента.")

    elif action == "back_to_menu":
        await show_foreman_menu(update, context)

    else:
        await query.edit_message_text("Неизвестное действие.")

# === ОБРАБОТКА СООБЩЕНИЙ ===
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()
    tools = load_json("data/tools.json")
    foremen = load_json("data/foremen.json")

    if context.user_data.get("transfer_stage") == "waiting_for_tool_id":
        tool = next((t for t in tools if t["id"] == text), None)

        if not tool:
            await update.message.reply_text("Инструмент с таким ID не найден.")
            return

        if tool.get("responsible_id") != user_id:
            await update.message.reply_text("Этот инструмент не прикреплён к тебе. Ты не можешь его передать.")
            return

        context.user_data["transfer_tool"] = tool
        context.user_data["transfer_stage"] = "select_receiver"

        buttons = []
        for f in foremen:
            if f["id"] != user_id:
                buttons.append([InlineKeyboardButton(f['name'], callback_data=f"give_to_{f['id']}")])

        buttons.append([InlineKeyboardButton("◀️ Назад", callback_data="back_to_menu")])

        await update.message.reply_text(
            f"Инструмент найден: {tool['name']} ({tool['object']})\n\nКому передаём?",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

# === ЗАПУСК ===
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start_command))
app.add_handler(CallbackQueryHandler(handle_callbacks))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

print("Бот запущен.")
app.run_polling()