from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes,
    CallbackQueryHandler, MessageHandler, filters
)
import json
import os
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
ITEMS_PER_PAGE = 10

def load_json(path):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Добро пожаловать в Plast Expert Tools!")
    user_id = update.effective_user.id
    foremen = load_json("data/foremen.json")
    users = load_json("data/users.json")

    for f in foremen:
        if f["id"] == user_id:
            await update.message.reply_text(f"Привет, {f['name']}! Ты зарегистрирован как бригадир.")
            return await show_foreman_menu(update, context)

    for u in users:
        if u["id"] == user_id and u["role"] == "Супервайзер":
            await update.message.reply_text(f"Добро пожаловать, {u['name']} (Супервайзер).")
            return

    await update.message.reply_text("Извините, вы не зарегистрированы в системе.")

async def show_foreman_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📋 Мои инструменты", callback_data="my_tools")],
        [InlineKeyboardButton("🔍 Весь инструмент", callback_data="all_tools_0")],
        [InlineKeyboardButton("📷 Сканировать QR", callback_data="scan_qr")]
    ]
    markup = InlineKeyboardMarkup(keyboard)
    if update.message:
        await update.message.reply_text("Выберите действие:", reply_markup=markup)
    elif update.callback_query:
        await update.callback_query.message.edit_text("Выберите действие:", reply_markup=markup)

async def handle_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    action = query.data

    if action == "back_to_menu":
        return await show_foreman_menu(update, context)

    if action == "scan_qr":
        context.user_data["awaiting_qr_scan"] = True
        await query.edit_message_text(
            "Сканируй QR-код — бот сразу покажет информацию.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="back_to_menu")]])
        )

    elif action == "my_tools":
        user_id = query.from_user.id
        tools = load_json("data/tools.json")
        user_tools = [t for t in tools if t.get("responsible_id") == user_id]
        if not user_tools:
            await query.edit_message_text("У тебя пока нет прикреплённых инструментов.",
                                          reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="back_to_menu")]]))
        else:
            msg = "Твои инструменты:"
            for t in user_tools:
                msg += f"• {t['name']} — {t['object']} ({t['status']})\n"
            await query.edit_message_text(msg,
                                          reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="back_to_menu")]]))

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    tools = load_json("data/tools.json")
    foremen = load_json("data/foremen.json")

    if context.user_data.get("awaiting_qr_scan"):
        context.user_data["awaiting_qr_scan"] = False
        tool = next((t for t in tools if str(t["id"]) == text), None)
        if not tool:
            await update.message.reply_text(
                "Инструмент не найден по этому QR.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Главная", callback_data="back_to_menu")]])
            )
            return

        responsible = tool.get("responsible") or next(
            (f["name"] for f in foremen if f["id"] == tool.get("responsible_id")), "не назначен"
        )
        msg = (
            f"Название: {tool['name']}\n"
            f"Объект: {tool['object']}\n"
            f"Статус: {tool['status']}\n"
            f"Ответственный: {responsible}"
        )
        await update.message.reply_text(
            msg,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Главная", callback_data="back_to_menu")]])
        )
        return

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start_command))
app.add_handler(CallbackQueryHandler(handle_callbacks))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

print("Бот запущен.")
app.run_polling()