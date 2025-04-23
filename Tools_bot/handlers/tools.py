from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import json
import os

from utils.json_utils import load_json, save_json


def find_user_role(user_id):
    foremen = load_json("data/foremen.json")
    users = load_json("data/users.json")

    for f in foremen:
        if f["id"] == user_id:
            return "foreman"
    for u in users:
        if u["id"] == user_id and u["role"] == "Супервайзер":
            return "supervisor"
    return None


async def handle_tool_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Введите ID инструмента:")
    context.user_data["awaiting_tool_id"] = True


async def process_tool_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("awaiting_tool_id"):
        return

    tool_id = update.message.text.strip()
    tools = load_json("data/tools.json")
    tool = next((t for t in tools if str(t.get("id")) == tool_id), None)

    if not tool:
        await update.message.reply_text("Инструмент с таким ID не найден.")
        context.user_data["awaiting_tool_id"] = False
        return

    context.user_data["awaiting_tool_id"] = False
    context.user_data["current_tool_id"] = tool_id
    user_id = update.effective_user.id
    role = find_user_role(user_id)

    responsible = tool.get("responsible") or "Не назначен"
    object_ = tool.get("object") or "Без объекта"
    status = tool.get("status") or "Не указан"

    msg = (
        f"Инструмент: {tool['name']}\n"
        f"Объект: {object_}\n"
        f"Статус: {status}\n"
        f"Ответственный: {responsible}"
    )

    buttons = [[InlineKeyboardButton("◀️ Назад", callback_data="back_to_menu")]]
    if role == "foreman":
        if not tool.get("responsible_id"):
            buttons.insert(0, [InlineKeyboardButton("✅ Стать ответственным", callback_data="become_responsible")])
        elif tool.get("responsible_id") == user_id:
            buttons.insert(0, [
                InlineKeyboardButton("📦 Оставить на складе", callback_data="return_to_warehouse"),
                InlineKeyboardButton("🔄 Передать", callback_data="transfer_tool")
            ])
        else:
            buttons.insert(0, [InlineKeyboardButton("📨 Запросить инструмент", callback_data="request_tool")])
    elif role == "supervisor":
        buttons.insert(0, [InlineKeyboardButton("👤 Назначить ответственного", callback_data="assign_responsible")])

    await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(buttons))