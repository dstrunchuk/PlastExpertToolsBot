from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
import os
import json
from handlers.tools import load_json, TOOLS_PATH, export_pending_to_excel
from handlers.database import get_all_tools

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
USERS_PATH = os.path.join(DATA_DIR, "users.json")

# Функция отображения главного меню
def load_json(filename):
    if not os.path.exists(filename):
        return []
    with open(filename, "r", encoding="utf-8") as f:
        return json.load(f)

from handlers.database import get_user_by_id
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = await get_user_by_id(user_id)

    # Если пользователь не найден — зарегистрировать его как Ответственного
    if not user:
        await update.message.reply_text("Сначала зарегистрируйтесь через /start.")
        return

    role = user.get("role", "Ответственный")

    buttons = []

    if role in ["Супервайзер", "Шеф", "Босс"]:
        buttons = [
            [InlineKeyboardButton("🔍 Найти инструмент", callback_data="find_tool")],
            [InlineKeyboardButton("🔨 Мои инструменты", callback_data="my_tools")],
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

# Мои инструменты
async def my_tools_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    user_id = update.effective_user.id

    tools = await get_all_tools()  # Теперь берём через базу!

    my_tools = [tool for tool in tools if tool.get("responsible_id") == user_id]

    if not my_tools:
        context.user_data["page_my_tools"] = 0
        keyboard = [
            [InlineKeyboardButton("◀️ Главное меню", callback_data="main_back")]
        ]
        await update.callback_query.edit_message_text(
            "У вас нет закрепленных инструментов.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    # Пагинация
    page = context.user_data.get("page_my_tools", 0)
    tools_per_page = 5
    start = page * tools_per_page
    end = start + tools_per_page
    current_tools = my_tools[start:end]

    if not current_tools:
        await update.callback_query.edit_message_text("Инструменты не найдены на этой странице.")
        return

    message = "Ваши инструменты:\n\n"
    for tool in current_tools:
        name = tool.get("name", "Без названия")
        tool_id = tool.get("id", "Без ID")
        responsible = tool.get("responsible", "Никто")
        object_name = tool.get("object", "Не указан")
        message += (f"*Название:* {name}\n"
                    f"*ID:* {tool_id}\n"
                    f"*Объект:* {object_name}\n"
                    f"*Ответственный:* {responsible}\n\n")

    buttons = []

    if start > 0:
        buttons.append(InlineKeyboardButton("◀️ Назад", callback_data="my_tools_prev"))
    if end < len(my_tools):
        buttons.append(InlineKeyboardButton("Вперёд ▶️", callback_data="my_tools_next"))

    buttons.append(InlineKeyboardButton("◀️ Главное меню", callback_data="main_back"))

    await update.callback_query.edit_message_text(message.strip(), parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([buttons]))

async def my_tools_prev(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["page_my_tools"] = max(context.user_data.get("page_my_tools", 0) - 1, 0)
    await my_tools_handler(update, context)

async def my_tools_next(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["page_my_tools"] = context.user_data.get("page_my_tools", 0) + 1
    await my_tools_handler(update, context)    

# НАЙТИ ИНСТРУМЕНТ
async def find_tool_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.edit_message_text("Введи ID или название инструмента:")

# ВСЕ ИНСТРУМЕНТЫ
async def all_tools_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()

    tools = await get_all_tools()

    if not tools:
        await update.callback_query.edit_message_text(
            "Инструменты не найдены.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Главное меню", callback_data="main_back")]])
        )
        return

    # Пагинация
    page = context.user_data.get("page_all_tools", 0)
    tools_per_page = 5
    start = page * tools_per_page
    end = start + tools_per_page
    current_tools = tools[start:end]

    if not current_tools:
        await update.callback_query.edit_message_text(
            "Инструменты не найдены на этой странице.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Главное меню", callback_data="main_back")]])
        )
        return

    message = "Список инструментов:\n\n"
    for tool in current_tools:
        name = tool.get("name", "Без названия")
        tool_id = tool.get("id", "Без ID")
        responsible = tool.get("responsible", "Никто")
        object_name = tool.get("object", "Не указан")

        message += (f"*Название:* {name}\n"
                    f"*ID:* {tool_id}\n"
                    f"*Объект:* {object_name}\n"
                    f"*Ответственный:* {responsible}\n\n")

    buttons = []

    if start > 0:
        buttons.append(InlineKeyboardButton("◀️ Назад", callback_data="all_tools_prev"))
    if end < len(tools):
        buttons.append(InlineKeyboardButton("Вперёд ▶️", callback_data="all_tools_next"))

    buttons.append(InlineKeyboardButton("◀️ Главное меню", callback_data="main_back"))

    await update.callback_query.edit_message_text(
        message.strip(),
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([buttons])
    )

async def all_tools_prev(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["page_all_tools"] = max(context.user_data.get("page_all_tools", 0) - 1, 0)
    await all_tools_handler(update, context)

async def all_tools_next(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["page_all_tools"] = context.user_data.get("page_all_tools", 0) + 1
    await all_tools_handler(update, context)

# ДОБАВИТЬ ИНСТРУМЕНТ
async def add_tool_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.edit_message_text("Добавление инструмента скоро будет доступно.")

# ЭКСПОРТ ВСЕГО
async def export_all_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.edit_message_text("Экспорт в Excel скоро будет доступен.")

# АДМИН-МЕНЮ
async def admin_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.edit_message_text("⚙️ Админ-панель в разработке.")