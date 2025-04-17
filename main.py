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
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_pending():
    return load_json("data/pending.json")

def save_pending(pending):
    save_json("data/pending.json", pending)

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

# === ОБРАБОТКА КНОПОК ===
async def handle_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    action = query.data
    user_id = query.from_user.id

    if action == "my_tools":
        tools = load_json("data/tools.json")
        my = [t for t in tools if t.get("responsible_id") == user_id]
        msg = "Твои инструменты:\n\n" if my else "У тебя нет прикреплённых инструментов."
        for t in my:
            msg += f"• {t['name']} — {t['object']} ({t['status']})\n"
        markup = InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="back_to_menu")]])
        await query.edit_message_text(msg, reply_markup=markup)

    elif action == "transfer_tool":
        await query.edit_message_text("Отправь ID инструмента, который хочешь передать.")
        context.user_data["transfer_stage"] = "waiting_for_tool_id"

    elif action.startswith("give_to_"):
        receiver_id = int(action.split("_")[-1])
        tool = context.user_data.get("transfer_tool")
        tool_id = str(tool["id"])  # Сохраняем как строку
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
        await query.edit_message_text("Запрос отправлен. Ожидаем подтверждения.")

    elif action.startswith("confirm_"):
        tool_id = action.split("_")[1]
        pending = load_pending()
        transfer = pending.get(tool_id)
        if not transfer:
            await query.edit_message_text("Передача не найдена или уже подтверждена.")
            return
        tools = load_json("data/tools.json")
        for t in tools:
            if str(t["id"]) == tool_id:
                t["responsible_id"] = user_id
        save_json("data/tools.json", tools)
        await query.edit_message_text("Инструмент успешно принят.")
        await context.bot.send_message(transfer["from_id"], "Инструмент передан и принят.")
        del pending[tool_id]
        save_pending(pending)

    elif action == "cancel_transfer":
        await query.edit_message_text("Передача отменена.")

    elif action == "back_to_menu":
        await show_foreman_menu(update, context)

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
        buttons.append([InlineKeyboardButton("◀️ Назад", callback_data="back_to_menu")])
        await update.message.reply_text(
            f"{tool['name']} ({tool['object']})\nКому передаём?",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

# === СТАРТ ===
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    foremen = load_json("data/foremen.json")
    if user_id in DEVELOPER_ID:
        await update.message.reply_text("Ты разработчик.")
        return
    for f in foremen:
        if f["id"] == user_id:
            await show_foreman_menu(update, context)
            return
    await update.message.reply_text("Ты не зарегистрирован.")

# === ЗАПУСК ===
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start_command))
app.add_handler(CallbackQueryHandler(handle_callbacks))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

print("Бот запущен.")
app.run_polling()