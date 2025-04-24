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

    if user_id == ADMIN_ID:
        await update.message.reply_text("Регистрация пропущена. Вы админ.")
        return

    if any(u["id"] == user_id for u in users):
        await update.message.reply_text("Вы уже зарегистрированы.")
        return

    await show_registration_menu(update)

async def show_registration_menu(update: Update):
    foremen = load_json(FOREMEN_PATH)
    foreman_names = sorted(set(f["name"] for f in foremen))
    supervisors = sorted(set(f["name"] for f in foremen if f["name"] in ["Aleksei Panin", "Shamil Kurbanov", "Juri Teras"]))
    director = ["Alexei"]

    buttons = []

    buttons += [[InlineKeyboardButton(name, callback_data=f"register:{name}")] for name in foreman_names if name not in supervisors + director]
    buttons.append([InlineKeyboardButton("— Супервайзеры —", callback_data="ignore")])
    buttons += [[InlineKeyboardButton(name, callback_data=f"register:{name}")] for name in supervisors]
    buttons.append([InlineKeyboardButton("— Шеф —", callback_data="ignore")])
    buttons += [[InlineKeyboardButton(name, callback_data=f"register:{name}")] for name in director]

    buttons.append([InlineKeyboardButton("Пропустить (Админ)", callback_data="register:ADMIN_SKIP")])

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

    if name == "ADMIN_SKIP":
        # Добавляем админа в users.json как шефа, если его там ещё нет
        if not any(u["id"] == user_id for u in users):
            users.append({"id": user_id, "name": "Admin", "role": "Шеф"})
            save_json(USERS_PATH, users)

        await query.edit_message_text("Регистрация пропущена. Вы админ.")
        # Переход в меню
        await show_main_menu(update, context)
        return

    role = "Супервайзер" if name in ["Aleksei Panin", "Shamil Kurbanov", "Juri Teras"] else "Ответственный"
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
    await show_main_menu(update, context)