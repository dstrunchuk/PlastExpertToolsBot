from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
import os
from handlers.database import get_all_tools, get_user_by_id, get_all_foremen
import pandas as pd
from telegram import InputFile
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import re

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = await get_user_by_id(user_id)

    # Если пользователь не найден — зарегистрировать его как Ответственного
    if not user:
        await update.message.reply_text("Сначала зарегистрируйтесь через /start.")
        return

    role = user.get("role", "Ответственный")

    buttons = []

    if role in ["Супервайзер", "Boss"]:
        buttons = [
            [InlineKeyboardButton("🔍 Найти инструмент", callback_data="find_tool")],
            [InlineKeyboardButton("🔨 Мои инструменты", callback_data="my_tools")],
            [InlineKeyboardButton("📋 Весь инструмент", callback_data="all_tools")],
            [InlineKeyboardButton("🧑‍🔧 Ответственные", callback_data="foremen_list")],  # <<< новая кнопка
            [InlineKeyboardButton("📥 Экспорт всего в Excel", callback_data="export_all")],
            [InlineKeyboardButton("➕ Добавить инструмент", callback_data="add_tool")],
            [InlineKeyboardButton("➕ Добавить ответственного", callback_data="add_foreman")],
           [InlineKeyboardButton("➕ Добавить объект", callback_data="add_object")]
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
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Главное меню:",
            reply_markup=InlineKeyboardMarkup([...])
        )

# Мои инструменты
async def my_tools_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    user_id = update.effective_user.id

    def escape_markdown(text: str) -> str:
        escape_chars = r'_*[]()~`>#+-=|{}.!'
        return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', text)

    tools = await get_all_tools()  # Теперь берём через базу!

    my_tools = [tool for tool in tools if str(tool.get("responsible_id")) == str(user_id)]

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
        name = escape_markdown(tool.get("name", "Без названия"))
        tool_id = escape_markdown(str(tool.get("id", "Без ID")))
        responsible = escape_markdown(tool.get("responsible", "Никто"))
        object_name = escape_markdown(tool.get("object", "Не указан"))
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

    # Отправляем НОВОЕ сообщение
    sent_message = await update.effective_chat.send_message(
        "Введи ID или название инструмента:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("◀️ Главное меню", callback_data="main_back")]
        ])
    )

    # Сохраняем ID нового сообщения в context.chat_data
    context.chat_data["find_prompt_message_id"] = sent_message.message_id

# ВСЕ ИНСТРУМЕНТЫ
async def all_tools_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    tools = await get_all_tools()

    if not tools:
        await update.callback_query.edit_message_text("Инструментов нет.")
        return

    page = context.user_data.get("page_all_tools", 0)
    tools_per_page = 5
    start = page * tools_per_page
    end = start + tools_per_page

    current_tools = tools[start:end]

    message = "Все инструменты:\n\n"
    for tool in current_tools:
        message += (
            f"Название: {tool.get('name', 'Без названия')}\n"
            f"ID: {tool.get('id', 'Нет ID')}\n"
            f"Объект: {tool.get('object', 'Не указан')}\n"
            f"Ответственный: {tool.get('responsible', 'Никто')}\n\n"
        )

    buttons = []

    if start > 0:
        buttons.append(InlineKeyboardButton("◀️ Назад", callback_data="all_tools_prev"))
    if end < len(tools):
        buttons.append(InlineKeyboardButton("Вперёд ▶️", callback_data="all_tools_next"))

    buttons.append(InlineKeyboardButton("◀️ Главное меню", callback_data="main_back"))

    await update.callback_query.edit_message_text(
        text=message.strip(),
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
    await update.callback_query.edit_message_text(
        "Добавление инструмента скоро будет доступно.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("◀️ Главное меню", callback_data="main_back")]
        ])
    )

# ЭКСПОРТ ВСЕГО
async def export_all_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()

    tools = await get_all_tools()

    if not tools:
        await update.callback_query.edit_message_text(
            "Нет доступных инструментов для экспорта.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("◀️ Главное меню", callback_data="main_back")]
            ])
        )
        return

    # Готовим данные для таблицы
    data = []
    for tool in tools:
        data.append({
            "Название": tool.get("name", "Без названия"),
            "ID": tool.get("id", "Без ID"),
            "Объект": tool.get("object", "Не указан"),
            "Ответственный": tool.get("responsible", "Никто")
        })

    df = pd.DataFrame(data)

    # Сохраняем файл временно
    file_path = "tools_export.xlsx"
    df.to_excel(file_path, index=False)

    # Отправляем файл пользователю
    await update.effective_chat.send_document(
        document=open(file_path, "rb"),
        filename="Инструменты.xlsx",
        caption="Экспорт всех инструментов."
    )

    # Удаляем файл после отправки
    try:
        os.remove(file_path)
    except Exception as e:
        print(f"Не удалось удалить файл: {e}")

# АДМИН-МЕНЮ
async def admin_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.edit_message_text("⚙️ Админ-панель в разработке.")


async def add_foreman_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(
        "Функция добавления ответственного скоро будет доступна.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("◀️ Главное меню", callback_data="main_back")]
        ])
    )

async def add_object_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(
        "Функция добавления объекта скоро будет доступна.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("◀️ Главное меню", callback_data="main_back")]
        ])
    )

async def foremen_list_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()

    foremen = await get_all_foremen()
    if not foremen:
        await update.callback_query.edit_message_text("Нет доступных ответственных.")
        return

    keyboard = []
    for foreman in foremen:
        keyboard.append([InlineKeyboardButton(foreman['name'], callback_data=f"foreman_tools:{foreman['id']}")])

    keyboard.append([InlineKeyboardButton("◀️ Главное меню", callback_data="main_back")])

    await update.callback_query.edit_message_text(
        "Выберите ответственного:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def show_foreman_tools_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    foreman_id = int(query.data.split(":")[1])

    tools = await get_all_tools()
    user_tools = [tool for tool in tools if tool.get("responsible_id") == foreman_id]

    if not user_tools:
        await query.edit_message_text(
            "У этого ответственного нет инструментов.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("◀️ Главное меню", callback_data="main_back")]
            ])
        )
        return

    message = f"Инструменты ответственного:\n\n"
    for tool in user_tools:
        message += (
            f"Название: {tool.get('name', 'Без названия')}\n"
            f"ID: {tool.get('id', 'Нет ID')}\n"
            f"Объект: {tool.get('object', 'Не указан')}\n\n"
        )

    await query.edit_message_text(
        text=message.strip(),
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("◀️ Главное меню", callback_data="main_back")]
        ])
    )