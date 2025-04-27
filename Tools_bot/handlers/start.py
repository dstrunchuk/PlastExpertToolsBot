from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from handlers.menu import show_main_menu
from handlers.database import get_user_by_id, save_user, get_all_foremen, update_foreman_id, add_foreman_if_missing, create_user
import os

ADMIN_ID = 987664835  # Твой ID админа

# /start команда
# /start команда
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_name = update.effective_user.full_name  # Получаем имя пользователя

    # Проверяем, существует ли уже пользователь в базе
    user = await get_user_by_id(user_id)

    if user:
        if user_id == ADMIN_ID:
            await send_message(update, "Вы зарегистрированы как админ. Можете выбрать роль снова.")
            await show_registration_menu(update)
        else:
            await send_message(update, "Вы уже зарегистрированы.")
            await show_main_menu(update, context)
        return
    
    # Пользователя нет — создаём
    await create_user(user_id, user_name)
    await save_user({"id": user_id, "name": user_name, "role": "Ответственный"})
    await send_message(update, "Вы успешно зарегистрированы!")
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
    users_data = [{"name": "Admin", "role": "Супервайзер", "id": ADMIN_ID}] + list(unique_names.values())

    buttons = []
    for user in users_data:
        if user["name"] == "Admin" and update.effective_user.id == ADMIN_ID:
            buttons.append([InlineKeyboardButton(f"{user['name']} (Вы)", callback_data=f"register:{user['name']}")])
        else:
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

    if name == "Admin" and user_id == ADMIN_ID:
        role = "Супервайзер"
        display_role = "супервайзер"
        name = update.effective_user.full_name
    elif found_user:
        role = found_user["role"]
        display_role = "супервайзер" if role == "Супервайзер" else "ответственный"
    else:
        role = "Ответственный"
        display_role = "ответственный"

    # Сохраняем пользователя
    await save_user({
        "id": user_id,
        "name": name,
        "role": role
    })

    # Обновляем foremen только если id ещё не проставлен
    if found_user and not found_user.get("id"):
        await update_foreman_id(name, user_id)

    await query.edit_message_text(f"Привет, {name}! Ты зарегистрирован как {display_role}.")
    await show_main_menu(update, context)

