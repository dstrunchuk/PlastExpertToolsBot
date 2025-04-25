from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
import os
import json

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
USERS_PATH = os.path.join(DATA_DIR, "users.json")

def load_json(filename):
    if not os.path.exists(filename):
        return []
    with open(filename, "r", encoding="utf-8") as f:
        return json.load(f)

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    users = load_json(USERS_PATH)
    user_data = next((u for u in users if u["id"] == user_id), None)

    if not user_data:
        if update.message:
            await update.message.reply_text("Сначала зарегистрируйся.")
        elif update.callback_query:
            await update.callback_query.edit_message_text("Сначала зарегистрируйся.")
        return

    role = user_data.get("role", "Ответственный")
    buttons = []

    if role in ["Супервайзер", "Шеф", "Босс"]:
        buttons = [
            [InlineKeyboardButton("🔍 Найти инструмент", callback_data="find_tool")],
            [InlineKeyboardButton("📋 Весь инструмент", callback_data="all_tools")],
            [InlineKeyboardButton("📥 Экспорт всего в Excel", callback_data="export_all")],
            [InlineKeyboardButton("➕ Добавить инструмент", callback_data="add_tool")]
        ]
    else:
        buttons = [
            [InlineKeyboardButton("🔍 Найти инструмент", callback_data="find_tool")],
            [InlineKeyboardButton("🔨 Мои инструменты", callback_data="my_tools")],
            [InlineKeyboardButton("➕ Добавить инструмент", callback_data="add_tool")]
        ]

    if update.message:
        await update.message.reply_text("Главное меню:", reply_markup=InlineKeyboardMarkup(buttons))
    elif update.callback_query:
        await update.callback_query.edit_message_text("Главное меню:", reply_markup=InlineKeyboardMarkup(buttons))