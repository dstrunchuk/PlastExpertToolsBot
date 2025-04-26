from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
import os
import json
from handlers.tools import load_json, TOOLS_PATH, export_pending_to_excel

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
USERS_PATH = os.path.join(DATA_DIR, "users.json")

# Функция отображения главного меню
async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    users = load_json(USERS_PATH)
    user_data = next((u for u in users if u["id"] == user_id), None)

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

# ==================== ОБРАБОТЧИКИ КНОПОК ====================

# Найти инструмент
async def find_tool_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.edit_message_text("Введи ID или название инструмента:")

# Весь инструмент
async def all_tools_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    tools = load_json(TOOLS_PATH)
    if not tools:
        await update.callback_query.edit_message_text("Инструменты не найдены.")
        return

    keyboard = []
    for idx, tool in enumerate(tools):
        tool_id = tool.get("id")
        if not tool_id or str(tool_id).lower() == "nan":
            callback_data = f"view_tool_by_index:{idx}"
            button_text = f"{tool.get('name', 'Без названия')} (без ID)"
        else:
            callback_data = f"view_tool:{tool_id}"
            button_text = f"{tool.get('name', 'Без названия')} (ID: {tool_id})"

        keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])

    await update.callback_query.edit_message_text("Все инструменты:", reply_markup=InlineKeyboardMarkup(keyboard))

# Мои инструменты
async def my_tools_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    user_id = update.effective_user.id
    tools = load_json(TOOLS_PATH)
    my_tools = [tool for tool in tools if tool.get("responsible_id") == user_id]

    if not my_tools:
        await update.callback_query.edit_message_text("У вас нет закрепленных инструментов.")
        return

    keyboard = []
    for idx, tool in enumerate(my_tools):
        tool_id = tool.get("id")
        if not tool_id or str(tool_id).lower() == "nan":
            callback_data = f"view_tool_by_index:{idx}"
            button_text = f"{tool.get('name', 'Без названия')} (без ID)"
        else:
            callback_data = f"view_tool:{tool_id}"
            button_text = f"{tool.get('name', 'Без названия')} (ID: {tool_id})"

        keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])

    await update.callback_query.edit_message_text("Ваши инструменты:", reply_markup=InlineKeyboardMarkup(keyboard))

# Добавить инструмент (заглушка)
async def add_tool_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.edit_message_text("Добавление инструмента скоро будет доступно.")

# Экспорт всего в Excel
async def export_all_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await export_pending_to_excel(update, context)

# Админ-панель (пока заглушка)
async def admin_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.edit_message_text("⚙️ Админ-панель в разработке.")