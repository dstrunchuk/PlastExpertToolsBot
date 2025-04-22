from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
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
    base_dir = os.path.join(os.path.dirname(__file__), "data")
    full_path = os.path.join(base_dir, os.path.basename(filename))
    if not os.path.exists(full_path):
        print(f"[Ошибка] Файл не найден: {full_path}")
        return []
    with open(full_path, "r", encoding="utf-8") as f:
        return json.load(f)

# === /start ===
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Добро пожаловать в Plast Expert Tools!")
    user_id = update.effective_user.id
    foremen = load_json("foremen.json")
    users = load_json("users.json")

    for f in foremen:
        if f["id"] == user_id:
            await update.message.reply_text(f"Привет, {f['name']}! Ты зарегистрирован как бригадир.")
            return await show_foreman_menu(update, context)

    for u in users:
        if u["id"] == user_id and u["role"] == "Супервайзер":
            await update.message.reply_text(f"Добро пожаловать, {u['name']} (Супервайзер).")
            return

    await update.message.reply_text("Извините, вы не зарегистрированы в системе.")

# === Меню бригадира ===
async def show_foreman_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📋 Мои инструменты", callback_data="my_tools")],
        [InlineKeyboardButton("🔍 Весь инструмент", callback_data="all_tools_0")],
        [InlineKeyboardButton("📷 Сканировать QR", web_app=WebAppInfo(url="https://plast-expert-tools-bot.vercel.app//"))]
    ]
    markup = InlineKeyboardMarkup(keyboard)
    if update.message:
        await update.message.reply_text("Выберите действие:", reply_markup=markup)
    elif update.callback_query:
        await update.callback_query.message.edit_text("Выберите действие:", reply_markup=markup)

# === Обработка кнопок ===
async def handle_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    action = query.data
    user_id = query.from_user.id

    if action == "back_to_menu":
        return await show_foreman_menu(update, context)

    elif action == "my_tools":
        tools = load_json("tools.json")
        user_tools = [t for t in tools if t.get("responsible_id") == user_id]
        if not user_tools:
            await query.edit_message_text("У тебя пока нет прикреплённых инструментов.",
                                      reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="back_to_menu")]]))
        else:
            msg = "Твои инструменты:\n\n"
            for t in user_tools:
                msg += (
                    f"• {t['name']}\n"
                    f"Объект: {t['object']}\n"
                    f"Статус: {t['status']}\n"
                    f"────────────\n"
                )
            await query.edit_message_text(msg,
                                          reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="back_to_menu")]]))
        
    elif action.startswith("all_tools_"):
        page = int(action.split("_")[-1])
        tools = load_json("tools.json")
        foremen = load_json("foremen.json")
        total_pages = (len(tools) - 1) // ITEMS_PER_PAGE + 1
        start = page * ITEMS_PER_PAGE
        end = start + ITEMS_PER_PAGE
        page_tools = tools[start:end]

        if not page_tools:
            await query.edit_message_text("Инструмент не найден.")
            return

        msg = f"Весь инструмент (страница {page+1} из {total_pages}):\n\n"
        for t in page_tools:
            responsible = t.get("responsible") or next(
                (f["name"] for f in foremen if f["id"] == t.get("responsible_id")), "не назначен"
            )
            msg += f"• {t['name']}\nОбъект: {t['object']}\nСтатус: {t['status']}\nОтветственный: {responsible}\n────────────\n"

        buttons = []
        if page > 0:
            buttons.append(InlineKeyboardButton("◀️ Назад", callback_data=f"all_tools_{page-1}"))
        if end < len(tools):
            buttons.append(InlineKeyboardButton("▶️ Далее", callback_data=f"all_tools_{page+1}"))
        buttons.append(InlineKeyboardButton("🏠 Главная", callback_data="back_to_menu"))

        await query.edit_message_text(
            msg,
            reply_markup=InlineKeyboardMarkup([buttons])
        )

# === Обработка сообщений (QR) ===
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    tools = load_json("tools.json")
    foremen = load_json("foremen.json")

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

async def handle_webapp_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = update.message.web_app_data.data
    tool_id = data.strip()

    tools = load_json("data/tools.json")
    foremen = load_json("data/foremen.json")
    tool = next((t for t in tools if str(t["id"]) == tool_id), None)

    if not tool:
        await update.message.reply_text("Инструмент не найден.")
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
    await update.message.reply_text(msg)

app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_webapp_data))

# === Запуск приложения ===
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start_command))
app.add_handler(CallbackQueryHandler(handle_callbacks))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

print("Бот запущен.")
app.run_polling()