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

    # Проверка, зарегистрирован ли пользователь
    if any(u["id"] == user_id for u in users):
        if user_id == ADMIN_ID:
            await update.message.reply_text("Вы зарегистрированы как админ. Можете выбрать роль снова.")
            await show_registration_menu(update)
        else:
            await update.message.reply_text("Вы уже зарегистрированы.")
            await show_main_menu(update, context)
        return

    await show_registration_menu(update)

async def show_registration_menu(update: Update):
    # Данные для выбора пользователей
    users_data = [
        {"name": "Admin", "role": "Супервайзер", "id": ADMIN_ID},
        {"name": "Sergei Strunchuk", "role": "Ответственный"},
        {"name": "Vladyslav Parkhomenko", "role": "Ответственный"},
        {"name": "Dmitri Kralya", "role": "Ответственный"},
        {"name": "Dmitri Karalko", "role": "Ответственный"},
        {"name": "Vitali Kulak", "role": "Ответственный"},
        {"name": "Oleh Kiekshyn", "role": "Ответственный"},
        {"name": "Aleksei Panin", "role": "Супервайзер"},
        {"name": "Shamil Kurbanov", "role": "Супервайзер"},
        {"name": "Juri Teras", "role": "Супервайзер"},
        {"name": "Alexei Dohin", "role": "Босс"}
    ]
    
    buttons = []
    for user in users_data:
        if user["role"] == "Супервайзер" and update.effective_user.id == ADMIN_ID and user["name"] == "Admin":
            buttons.append([InlineKeyboardButton(f"{user['name']} (Вы)", callback_data=f"register:{user['name']}")])
        else:
            buttons.append([InlineKeyboardButton(user['name'], callback_data=f"register:{user['name']}")])

    await update.message.reply_text(
        "Выбери своё имя для регистрации:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

async def handle_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    name = query.data.split(":")[1]

    users = load_json(USERS_PATH)

    if name == "Admin" and user_id == ADMIN_ID:
        role = "Супервайзер"
        display_role = "супервайзер"
        name = update.effective_user.full_name  # Можешь оставить "Admin" или заменить на своё реальное имя
    elif name == "Alexei Dohin":
        role = "Супервайзер"
        display_role = "босс"
    elif name in ["Aleksei Panin", "Shamil Kurbanov", "Juri Teras"]:
        role = "Супервайзер"
        display_role = "супервайзер"
    else:
        role = "Ответственный"
        display_role = "ответственный"

    # Удаляем старую запись, если есть
    users = [u for u in users if u["id"] != user_id]
    users.append({"id": user_id, "name": name, "role": role})
    save_json(USERS_PATH, users)

    # Обновляем foremen.json (если нужно)
    foremen = load_json(FOREMEN_PATH)
    found = False
    for f in foremen:
        if f["name"] == name:
            f["id"] = user_id
            found = True
            break
    if not found and role in ["Ответственный", "Супервайзер"]:
        foremen.append({"name": name, "role": role, "id": user_id})
    save_json(FOREMEN_PATH, foremen)

    await query.edit_message_text(f"Привет, {name}! Ты зарегистрирован как {display_role}.")
    await show_main_menu(update, context)