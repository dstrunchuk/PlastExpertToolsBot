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

    # Если пользователь не найден — регистрируем автоматически как Ответственного
    if not user_data:
        new_user = {
            "id": user_id,
            "name": update.effective_user.full_name,
            "role": "Ответственный"
        }
        users.append(new_user)
        with open(USERS_PATH, "w", encoding="utf-8") as f:
            json.dump(users, f, ensure_ascii=False, indent=2)
        user_data = new_user

    role = user_data.get("role", "Ответственный")
    buttons = []

    if role in ["Супервайзер", "Шеф", "Босс"]:
        buttons = [
            [InlineKeyboardButton("🔍 Найти инструмент", callback_data="find_tool")],
            [InlineKeyboardButton("📋 Весь инструмент", callback_data="all_tools")],
            [InlineKeyboardButton("📥 Экспорт всего в Excel", callback_data="export_all")],
            [InlineKeyboardButton("➕ Добавить инструмент", callback_data="add_tool")]
        ]
    elif role == "Админ":
        buttons = [
            [InlineKeyboardButton("⚙️ Админка", callback_data="admin_menu")],
            [InlineKeyboardButton("🔍 Найти инструмент", callback_data="find_tool")],
            [InlineKeyboardButton("🔨 Мои инструменты", callback_data="my_tools")],
            [InlineKeyboardButton("➕ Добавить инструмент", callback_data="add_tool")]
        ]
    else:
        buttons = [
            [InlineKeyboardButton("🔍 Найти инструмент", callback_data="find_tool")],
            [InlineKeyboardButton("🔨 Мои инструменты", callback_data="my_tools")],
            [InlineKeyboardButton("➕ Добавить инструмент", callback_data="add_tool")]
        ]

    menu_text = "Главное меню. Выберите действие:"

    if update.message:
        await update.message.reply_text(menu_text, reply_markup=InlineKeyboardMarkup(buttons))
    elif update.callback_query:
        await update.callback_query.edit_message_text(menu_text, reply_markup=InlineKeyboardMarkup(buttons))