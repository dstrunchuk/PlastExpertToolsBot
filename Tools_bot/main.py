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
ITEMS_PER_PAGE = 5

def load_json(filename):
    path = os.path.join(os.path.dirname(__file__), "data", filename)
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# === /start ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    context.user_data["id"] = user_id
    context.user_data["page"] = 0

    foremen = load_json("foremen.json")
    users = load_json("users.json")

    for f in foremen:
        if f["id"] == user_id:
            context.user_data["role"] = "foreman"
            return await show_menu(update, context, "foreman")

    for u in users:
        if u["id"] == user_id and u["role"] == "Супервайзер":
            context.user_data["role"] = "supervisor"
            return await show_menu(update, context, "supervisor")

    await update.message.reply_text("Извините, вы не зарегистрированы.")

# === МЕНЮ ===
async def show_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, role: str):
    keyboard = [
        [InlineKeyboardButton("📋 Мои инструменты", callback_data="my_tools")],
        [InlineKeyboardButton("🔍 Весь инструмент", callback_data="all_tools_0")],
        [InlineKeyboardButton("🆔 Найти по ID", callback_data="search_tool")]
    ]
    if update.message:
        await update.message.reply_text("Выберите действие:", reply_markup=InlineKeyboardMarkup(keyboard))
    elif update.callback_query:
        await update.callback_query.message.edit_text("Выберите действие:", reply_markup=InlineKeyboardMarkup(keyboard))

# === ОБРАБОТКА КНОПОК ===
async def handle_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    user_id = context.user_data.get("id")
    role = context.user_data.get("role")
    tools = load_json("tools.json")
    foremen = load_json("foremen.json")

    if data == "my_tools":
        my = [t for t in tools if t.get("responsible_id") == user_id]
        if not my:
            await query.edit_message_text("У тебя пока нет инструментов.",
                                          reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="back")]]))
        else:
            msg = "Твои инструменты:\n\n"
            for t in my:
                msg += f"— {t['name']}\nОбъект: {t['object']}\nСтатус: {t['status']}\n\n"
            await query.edit_message_text(msg.strip(),
                                          reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="back")]]))

    elif data.startswith("all_tools_"):
        page = int(data.split("_")[-1])
        context.user_data["page"] = page
        start_i = page * ITEMS_PER_PAGE
        end_i = start_i + ITEMS_PER_PAGE
        chunk = tools[start_i:end_i]
        total = len(tools)

        if not chunk:
            await query.edit_message_text("Инструментов нет.",
                                          reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="back")]]))
            return

        msg = f"Инструменты ({start_i + 1}–{min(end_i, total)} из {total}):\n\n"
        for t in chunk:
            resp = next((f["name"] for f in foremen if f["id"] == t.get("responsible_id")), "не назначен")
            msg += f"— {t['name']}\nОбъект: {t['object']}\nСтатус: {t['status']}\nОтветственный: {resp}\n\n"

        buttons = []
        if page > 0:
            buttons.append(InlineKeyboardButton("⬅️ Назад", callback_data=f"all_tools_{page - 1}"))
        if end_i < total:
            buttons.append(InlineKeyboardButton("➡️ Далее", callback_data=f"all_tools_{page + 1}"))
        buttons.append(InlineKeyboardButton("🏠 Главная", callback_data="back"))
        await query.edit_message_text(msg.strip(), reply_markup=InlineKeyboardMarkup([buttons]))

    elif data == "search_tool":
        context.user_data["awaiting_tool_id"] = True
        await query.edit_message_text("Введите ID инструмента, чтобы найти его.",
                                      reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="back")]]))

    elif data == "back":
        return await show_menu(update, context, role)

# === ПОИСК ПО ID ===
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("awaiting_tool_id"):
        tool_id = update.message.text.strip()
        tools = load_json("tools.json")
        foremen = load_json("foremen.json")
        role = context.user_data.get("role")
        user_id = context.user_data.get("id")

        tool = next((t for t in tools if str(t["id"]) == tool_id), None)
        if not tool:
            await update.message.reply_text("Инструмент не найден.",
                                            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="back")]]))
            return

        resp = next((f["name"] for f in foremen if f["id"] == tool.get("responsible_id")), "не назначен")
        msg = f"Инструмент найден:\n\n— {tool['name']}\nОбъект: {tool['object']}\nСтатус: {tool['status']}\nОтветственный: {resp}"

        if role == "supervisor":
            msg += "\n\nВы можете изменить ответственного."
        elif role == "foreman":
            if tool.get("responsible_id") == user_id:
                msg += "\n\nТы владелец — можешь передать."
            else:
                msg += "\n\nТы можешь запросить передачу."

        context.user_data["awaiting_tool_id"] = False
        await update.message.reply_text(msg,
                                        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="back")]]))
    else:
        await update.message.reply_text("Напиши команду /start.")

# === ЗАПУСК ===
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(handle_callbacks))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

print("Бот запущен.")
app.run_polling()