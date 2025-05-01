from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from handlers.menu import show_main_menu
from handlers.database import get_user_by_id, save_user, get_all_foremen, update_foreman_id, add_foreman_if_missing, create_user, get_all_tools, update_tool
import os

# /start команда
# /start команда
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    # Проверяем, существует ли уже пользователь в базе
    user = await get_user_by_id(user_id)

    if user:
        # Если пользователь уже зарегистрирован
        await send_message(update, "Вы уже зарегистрированы.")
        await show_main_menu(update, context)
        return
    
    # Пользователь НЕ найден — отправляем меню выбора имени
    await send_message(update, "Добро пожаловать! Пожалуйста, выберите своё имя для регистрации.")
    await show_registration_menu(update)

# Отправка сообщения или изменение сообщения
async def send_message(update: Update, text: str):
    if update.message:
        await update.message.reply_text(text)
    elif update.callback_query:
        await update.callback_query.edit_message_text(text)

# Меню выбора имени
async def show_registration_menu(update: Update):
    foremen = await get_all_foremen()

    # Убираем всех, у кого имя Admin
    foremen = [f for f in foremen if f["name"] != "Admin"]

    # Оставляем только уникальные имена
    unique_names = {}
    for f in foremen:
        unique_names[f["name"]] = f

    # Готовим список для кнопок
    users_data = list(unique_names.values())  # Без "Admin"

    buttons = []
    for user in users_data:
        buttons.append([InlineKeyboardButton(user['name'], callback_data=f"register:{user['name']}")])

    await update.message.reply_text(
        "Выбери своё имя для регистрации:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

# Обработка выбора имени
async def handle_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    name = query.data.split(":")[1]

    foremen = await get_all_foremen()
    found_user = next((f for f in foremen if f["name"] == name), None)

    if found_user:
        role = found_user["role"]
        display_role = "супервайзер" if role == "Супервайзер" else "ответственный"
    else:
        role = "Ответственный"
        display_role = "ответственный"

    await save_user({
        "id": user_id,
        "name": name,
        "role": role
    })

    # Обновляем foremen только если id ещё не проставлен
    if found_user and not found_user.get("id"):
        await update_foreman_id(name, user_id)

    # Ищем все инструменты, где responsible совпадает с его именем И НЕТ responsible_id
    assigned_count = 0

    # Используем выбранное имя из кнопки, а не имя в Telegram!
    tools = await get_all_tools()
    for tool in tools:
        responsible = tool.get("responsible")
        print(f"[Проверка имени] '{responsible.strip().lower()}' == '{name.strip().lower()}'")
        if responsible and responsible.strip().lower() == name.strip().lower() and not tool.get("responsible_id", None):
            tool["responsible_id"] = user_id  # <== вот это нужно!
            await update_tool(tool)
            assigned_count += 1

    # После обновления всех инструментов — проверка через вывод
    tools_check = await get_all_tools()
    for tool in tools_check:
        if tool.get("responsible_id") == user_id:
            print(f"Инструмент закреплён: {tool.get('name')} (ID: {tool.get('id')}) за {user_id}")

    try:
        await query.edit_message_text(
            f"Привет, {name}! Ты зарегистрирован как {display_role}.\n"
            f"На тебя закреплено {assigned_count} инструмент(ов)."
        )
    except Exception as e:
        print(f"[!] Ошибка при выводе финального сообщения: {e}")

    await show_main_menu(update, context)
    


async def assign_tools_to_user(user_id, user_name):
    tools = await get_all_tools()

    for tool in tools:
        if tool.get("responsible") == user_name and not tool.get("responsible_id"):
            tool["responsible_id"] = user_id
            await update_tool(tool)
