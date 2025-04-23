from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes,
    CallbackQueryHandler, MessageHandler, filters
)
import os
import json
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
ITEMS_PER_PAGE = 5

def load_json(file):
    with open(os.path.join("data", file), encoding="utf-8") as f:
        return json.load(f)

def save_json(file, data):
    with open(os.path.join("data", file), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    foremen = load_json("foremen.json")
    users = load_json("users.json")

    for f in foremen:
        if f["id"] == user_id:
            return await show_foreman_menu(update, context)

    for u in users:
        if u["id"] == user_id and u["role"] == "Супервайзер":
            return await show_supervisor_menu(update, context)

    await update.message.reply_text("Извините, вы не зарегистрированы.")

async def show_foreman_menu(update, context):
    keyboard = [
        [InlineKeyboardButton("📋 Мои инструменты", callback_data="my_tools")],
        [InlineKeyboardButton("📦 Весь инструмент", callback_data="all_tools_0")],
        [InlineKeyboardButton("🔍 Найти по ID", callback_data="search_tool")]
    ]
    markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Меню бригадира:", reply_markup=markup)

async def show_supervisor_menu(update, context):
    keyboard = [
        [InlineKeyboardButton("📦 Весь инструмент", callback_data="all_tools_0")],
        [InlineKeyboardButton("🔍 Найти по ID", callback_data="search_tool")]
    ]
    markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Меню супервайзера:", reply_markup=markup)

async def handle_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    if query.data.startswith("all_tools_"):
        tools = load_json("tools.json")
        page = int(query.data.split("_")[-1])
        start = page * ITEMS_PER_PAGE
        end = start + ITEMS_PER_PAGE
        msg = "\n\n".join(
            f"🔧 {t['name']}\nОбъект: {t['object']}\nСтатус: {t['status']}\nОтветственный: {t.get('responsible', 'не назначен')}"
            for t in tools[start:end]
        ) or "Нет инструментов на этой странице."

        nav = []
        if start > 0:
            nav.append(InlineKeyboardButton("◀️ Назад", callback_data=f"all_tools_{page - 1}"))
        if end < len(tools):
            nav.append(InlineKeyboardButton("▶️ Далее", callback_data=f"all_tools_{page + 1}"))
        nav.append(InlineKeyboardButton("◀️ Главная", callback_data="back_menu"))

        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup([nav]))

    elif query.data == "back_menu":
        foremen = load_json("foremen.json")
        if any(f["id"] == user_id for f in foremen):
            await show_foreman_menu(update, context)
        else:
            await show_supervisor_menu(update, context)

    elif query.data == "my_tools":
        tools = load_json("tools.json")
        my = [t for t in tools if t.get("responsible_id") == user_id]
        msg = "\n\n".join(f"🔧 {t['name']}\nОбъект: {t['object']}\nСтатус: {t['status']}" for t in my) or "Инструментов нет."
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("◀️ Назад", callback_data="back_menu")]
        ]))

    elif query.data == "search_tool":
        context.user_data["awaiting_search"] = True
        await query.edit_message_text("Введите ID инструмента для поиска:")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()
    if context.user_data.get("awaiting_search"):
        tools = load_json("tools.json")
        tool = next((t for t in tools if str(t["id"]) == text), None)
        if not tool:
            await update.message.reply_text("Инструмент не найден.")
            return
        buttons = [[InlineKeyboardButton("◀️ Главная", callback_data="back_menu")]]
        if tool.get("responsible_id") is None:
            buttons.insert(0, [InlineKeyboardButton("Стать ответственным", callback_data=f"take_{tool['id']}")])
        elif tool.get("responsible_id") != user_id:
            buttons.insert(0, [InlineKeyboardButton("Запросить инструмент", callback_data=f"request_{tool['id']}")])
        msg = f"🔧 {tool['name']}\nОбъект: {tool['object']}\nСтатус: {tool['status']}\nОтветственный: {tool.get('responsible', 'не назначен')}"
        await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(buttons))
        context.user_data["awaiting_search"] = False

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(handle_callbacks))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

print("Бот запущен.")
app.run_polling()