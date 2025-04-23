from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import json
import os

ADMIN_ID = 987664835  # Твой Telegram ID

def load_json(path):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    registered_users = load_json("data/users.json")

    # Если админ — всегда показать меню
    if user_id == ADMIN_ID:
        return await show_registration_menu(update)

    # Если уже зарегистрирован
    for user in registered_users:
        if user["id"] == user_id:
            await update.message.reply_text("Вы уже зарегистрированы.")
            return

    return await show_registration_menu(update)

aasync def show_registration_menu(update: Update):
    keyboard = [
        [InlineKeyboardButton("— Ответственные —", callback_data="none")],
        [InlineKeyboardButton("Sergei Strunchuk", callback_data="reg_Sergei Strunchuk")],
        [InlineKeyboardButton("Vladyslav Parkhomenko", callback_data="reg_Vladyslav Parkhomenko")],
        [InlineKeyboardButton("Dmitri Kralya", callback_data="reg_Dmitri Kralya")],
        [InlineKeyboardButton("Dmitri Karalko", callback_data="reg_Dmitri Karalko")],
        [InlineKeyboardButton("Vitali Kulak", callback_data="reg_Vitali Kulak")],
        [InlineKeyboardButton("Oleh Kiekshyn", callback_data="reg_Oleh Kiekshyn")],
        [InlineKeyboardButton("— Супервайзеры —", callback_data="none")],
        [InlineKeyboardButton("Aleksei Panin", callback_data="reg_Aleksei Panin")],
        [InlineKeyboardButton("Shamil Kurbanov", callback_data="reg_Shamil Kurbanov")],
        [InlineKeyboardButton("Juri Teras", callback_data="reg_Juri Teras")],
        [InlineKeyboardButton("— Шеф —", callback_data="none")],
        [InlineKeyboardButton("Alexei", callback_data="reg_Alexei")],
        [InlineKeyboardButton("⏭ Пропустить (для админа)", callback_data="skip_admin")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Выберите своё имя:", reply_markup=reply_markup)

async def handle_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    full_name = query.from_user.full_name

    if query.data == "skip_admin":
        await query.edit_message_text("Регистрация пропущена. Вы админ.")
        return

    selected_name = query.data.replace("reg_", "")

    new_user = {
        "id": user_id,
        "name": selected_name,
        "full_name": full_name,
        "role": "Супервайзер" if selected_name in [
            "Aleksei Panin", "Shamil Kurbanov", "Juri Teras"
        ] else "Ответственный"
    }

    users = load_json("data/users.json")
    if not any(u["id"] == user_id for u in users):
        users.append(new_user)
        save_json("data/users.json", users)

    await query.edit_message_text(f"Регистрация завершена, {selected_name}.")