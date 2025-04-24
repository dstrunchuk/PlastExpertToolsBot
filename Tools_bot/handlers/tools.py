from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import os
import json

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
TOOLS_PATH = os.path.join(DATA_DIR, "tools.json")
USERS_PATH = os.path.join(DATA_DIR, "users.json")

def load_json(filename):
    if not os.path.exists(filename):
        return []
    with open(filename, "r", encoding="utf-8") as f:
        return json.load(f)

async def handle_tool_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.edit_message_text("Введи ID инструмента:")

async def process_tool_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    tool_id = update.message.text.strip()

    tools = load_json(TOOLS_PATH)
    users = load_json(USERS_PATH)
    user = next((u for u in users if u["id"] == user_id), None)
    role = user.get("role", "Ответственный") if user else "Ответственный"

    tool = next((t for t in tools if str(t.get("id")) == tool_id), None)

    if not tool:
        await update.message.reply_text("Инструмент с таким ID не найден.")
        return

    responsible = tool.get("responsible")
    responsible_id = tool.get("responsible_id")

    text = f"**Инструмент:** {tool.get('name')}\n"
    text += f"**ID:** {tool.get('id')}\n"
    text += f"**Объект:** {tool.get('object') or '—'}\n"
    text += f"**Ответственный:** {responsible or 'Никто'}"

    buttons = []

    if role in ["Супервайзер", "Шеф"]:
        buttons.append([InlineKeyboardButton("👤 Назначить ответственного", callback_data=f"assign:{tool_id}")])

    elif role == "Ответственный":
        if responsible_id is None:
            buttons.append([InlineKeyboardButton("✅ Стать ответственным", callback_data=f"take:{tool_id}")])
        elif responsible_id == user_id:
            buttons.append([
                InlineKeyboardButton("📤 Передать", callback_data=f"transfer:{tool_id}"),
                InlineKeyboardButton("🏬 Оставить на складе", callback_data=f"store:{tool_id}")
            ])
        else:
            buttons.append([InlineKeyboardButton("📥 Запросить передачу", callback_data=f"request:{tool_id}")])

    buttons.append([InlineKeyboardButton("◀️ Главная", callback_data="main_back")])

    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode="Markdown"
    )