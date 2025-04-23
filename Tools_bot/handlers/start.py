# handlers/start.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import json
import os

ADMIN_ID = 987664835

def load_foremen():
    with open("data/foremen.json", encoding="utf-8") as f:
        return json.load(f)

def save_foremen(data):
    with open("data/foremen.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_name = update.effective_user.full_name
    foremen = load_foremen()

    # Проверяем, зарегистрирован ли уже
    for f in foremen:
        if f.get("id") == user_id:
            await update.message.reply_text(
                f"Привет, {f['name']}! Ты уже зарегистрирован.",
            )
            return await context.bot.send_message(chat_id=user_id, text="Меню будет добавлено позже.")

    # Кнопки выбора имени
    buttons = [
        [InlineKeyboardButton(f["name"], callback_data=f"reg_{f['name']}")] for f in foremen if f.get("id") is None
    ]

    # Если ты админ — добавляем кнопку пропустить
    if user_id == ADMIN_ID:
        buttons.append([InlineKeyboardButton("⏭ Пропустить (тест админ)", callback_data="skip_admin")])

    await update.message.reply_text(
        "Выберите своё имя из списка для регистрации:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

async def handle_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data == "skip_admin" and user_id == ADMIN_ID:
        await query.edit_message_text("Пропущено. Ты вошёл как админ. Полный доступ открыт.")
        return await context.bot.send_message(chat_id=user_id, text="(Здесь будет меню разработчика)")

    if query.data.startswith("reg_"):
        name = query.data[4:]
        foremen = load_foremen()

        for f in foremen:
            if f["name"] == name and not f.get("id"):
                f["id"] = user_id
                save_foremen(foremen)
                await query.edit_message_text(f"Добро пожаловать, {name}! Регистрация завершена.")
                return await context.bot.send_message(chat_id=user_id, text="(Здесь будет меню бригадира/супервайзера)")

        await query.edit_message_text("Имя уже зарегистрировано или ошибка.")