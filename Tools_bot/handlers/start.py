from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from handlers.menu import show_main_menu
import json
import os

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
FOREMEN_PATH = os.path.join(DATA_DIR, "foremen.json")
USERS_PATH = os.path.join(DATA_DIR, "users.json")
ADMIN_ID = 987664835

def load_json(filename):
    if not os.path.exists(filename):
        return []
    with open(filename, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    users = load_json(USERS_PATH)

    if any(u["id"] == user_id for u in users):
        if user_id == ADMIN_ID:
            await update.message.reply_text("Вы зарегистрированы как админ. Можешь выбрать роль снова.")
            await show_registration_menu(update)
        else:
            await update.message.reply_text("Вы уже зарегистрированы.")
            await show_main_menu(update, context)
        return

    await show_registration_menu(update)

async def show_registration_menu(update: Update):
    foremen = load_json(FOREMEN_PATH)
    foreman_names = sorted(set(f["name"] for f in foremen))
    supervisors = sorted(set(f["name"] for f in foremen if f["name"] in ["Aleksei Panin", "Shamil Kurbanov", "Juri Teras"]))
    director = ["Alexei"]

    buttons = []

    # Список всех ответственных (не супервайзеров и шефов)
    buttons += [[InlineKeyboardButton(name, callback_data=f"register:{name}")] for name in foreman_names if name not in supervisors + director]
    
    buttons.append([InlineKeyboardButton("— Супервайзеры —", callback_data="ignore")])
    buttons += [[InlineKeyboardButton(name, callback_data=f"register:{name}")] for name in supervisors]
    
    buttons.append([InlineKeyboardButton("— Шеф —", callback_data="ignore")])
    buttons += [[InlineKeyboardButton(name, callback_data=f"register:{name}")] for name in director]

    buttons.append([InlineKeyboardButton("Пропустить (Админ)", callback_data="register:ADMIN_SKIP")])

    # Добавляем кнопку для админа
    if update.effective_user.id == ADMIN_ID:
        buttons.append([InlineKeyboardButton("Войти как...", callback_data="register:admin_choose_role")])

    await update.message.reply_text(
        "Выбери своё имя для регистрации:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )
async def handle_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    parts = query.data.split(":")
    name = parts[1]

    users = load_json(USERS_PATH)

    # Если выбрана роль "ADMIN_SKIP", пропускаем регистрацию, добавляем админа как ответственного
    if name == "ADMIN_SKIP":
        if not any(u["id"] == user_id for u in users):
            users = [u for u in users if u["id"] != user_id]  # Удаляем старую запись, если админ перезаходит под другой ролью
            users.append({"id": user_id, "name": "Admin", "role": "Ответственный"})  # Принудительно ставим роль "Ответственный"
            save_json(USERS_PATH, users)

        await query.edit_message_text("Регистрация пропущена. Вы админ.")
        await show_main_menu(update, context)  # Переводим на основное меню
        return

    # Если выбрана роль через "Войти как...", показываем выбор роли
    if name == "admin_choose_role":
        buttons = [
            [InlineKeyboardButton("✅ Ответственный", callback_data="register:Admin:Ответственный")],
            [InlineKeyboardButton("✅ Супервайзер", callback_data="register:Admin:Супервайзер")],
            [InlineKeyboardButton("✅ Шеф", callback_data="register:Admin:Шеф")],
            [InlineKeyboardButton("◀️ Назад", callback_data="register:back_to_main")]
        ]
        await query.edit_message_text("Кем войти?", reply_markup=InlineKeyboardMarkup(buttons))
        return

    # Для других пользователей — ставим роль в зависимости от их имени
    role = "Ответственный"  # Роль по умолчанию
    if name in ["Aleksei Panin", "Shamil Kurbanov", "Juri Teras"]:  # Устанавливаем роль супервайзера
        role = "Супервайзер"

    # Добавляем пользователя с его ролью
    users.append({"id": user_id, "name": name, "role": role})
    save_json(USERS_PATH, users)

    # Добавляем Telegram ID в foremen.json
    foremen = load_json(FOREMEN_PATH)
    for f in foremen:
        if f["name"] == name:
            f["id"] = user_id
            break
    save_json(FOREMEN_PATH, foremen)

    await query.edit_message_text(f"Привет, {name}! Ты зарегистрирован как {role}.")
    await show_main_menu(update, context)  # Переводим на основное меню