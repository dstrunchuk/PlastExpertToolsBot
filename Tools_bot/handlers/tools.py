from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import json
import os

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
TOOLS_PATH = os.path.join(DATA_DIR, "tools.json")
USERS_PATH = os.path.join(DATA_DIR, "users.json")

def load_json(filename):
    if not os.path.exists(filename):
        return []
    with open(filename, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

async def handle_tool_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    action = query.data.split(":")[0]
    tool_id = query.data.split(":")[1]
    
    tools = load_json(TOOLS_PATH)
    users = load_json(USERS_PATH)
    
    tool = next((t for t in tools if str(t.get("id")) == tool_id), None)
    user = next((u for u in users if u["id"] == user_id), None)
    role = user.get("role", "Ответственный") if user else "Ответственный"
    
    if not tool:
        await query.edit_message_text("Инструмент не найден.")
        return

    responsible_id = tool.get("responsible_id")
    
    # Обработка действия: Стать ответственным
    if action == "take":
        if responsible_id is None:
            tool["responsible_id"] = user_id
            tool["responsible"] = user["name"]
            save_json(TOOLS_PATH, tools)
            await query.edit_message_text(f"Теперь вы ответственны за {tool['name']}.")
        else:
            await query.edit_message_text(f"Инструмент уже закреплен за {tool['responsible']}.")
    
    # Обработка действия: Передача инструмента
    elif action == "transfer":
        if responsible_id != user_id:  # Только если инструмент не ваш
            tool["responsible_id"] = user_id
            tool["responsible"] = user["name"]
            save_json(TOOLS_PATH, tools)
            await query.edit_message_text(f"Инструмент {tool['name']} передан вам.")
        else:
            await query.edit_message_text(f"Инструмент уже ваш.")
    
    # Обработка действия: Вернуть на склад
    elif action == "store":
        if responsible_id is not None:  # Если инструмент закреплён за кем-то
            tool["responsible_id"] = None
            tool["responsible"] = None
            tool["object"] = "Ladu"  # Если склад — это 'Ladu'
            save_json(TOOLS_PATH, tools)
            await query.edit_message_text(f"Инструмент {tool['name']} возвращен на склад.")
        else:
            await query.edit_message_text(f"Инструмент уже на складе.")
    
    # Обработка действия: Запросить передачу
    elif action == "request":
        if responsible_id:
            responsible_user = next(u for u in users if u["id"] == responsible_id)
            await query.edit_message_text(f"Вы запросили передачу инструмента {tool['name']} у {responsible_user['name']}.")
        else:
            await query.edit_message_text(f"Инструмент {tool['name']} ещё не закреплен за кем-либо.")