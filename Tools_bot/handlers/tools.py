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

# Обработчик для поиска ID инструмента
async def process_tool_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    tool_id = update.message.text.strip()  # Получаем ID инструмента

    tools = load_json(TOOLS_PATH)
    tool = next((t for t in tools if str(t.get("id")) == tool_id), None)

    if not tool:
        await update.message.reply_text("Инструмент с таким ID не найден.")
        return

    # Если инструмент найден, показываем его данные и кнопки для действий
    await handle_tool_action(update, context, tool_id)

# Обработчик для всех действий с инструментом
async def handle_tool_action(update: Update, context: ContextTypes.DEFAULT_TYPE, tool_id=None):
    if not tool_id:  # Если ID не передан, то находим его из контекста
        tool_id = update.callback_query.data.split(":")[1]
    
    user_id = update.callback_query.from_user.id if update.callback_query else update.effective_user.id
    action = update.callback_query.data.split(":")[0] if update.callback_query else None

    tools = load_json(TOOLS_PATH)
    users = load_json(USERS_PATH)

    tool = next((t for t in tools if str(t.get("id")) == tool_id), None)
    user = next((u for u in users if u["id"] == user_id), None)
    role = user.get("role", "Ответственный") if user else "Ответственный"

    if not tool:
        await update.message.reply_text("Инструмент не найден.")
        return

    responsible_id = tool.get("responsible_id")

    # Стать ответственным
    if action == "take":
        if responsible_id is None:
            tool["responsible_id"] = user_id
            tool["responsible"] = user["name"]
            save_json(TOOLS_PATH, tools)
            await update.callback_query.edit_message_text(f"Теперь вы ответственны за {tool['name']}.")
        else:
            await update.callback_query.edit_message_text(f"Инструмент уже закреплен за {tool['responsible']}.")

    # Передача инструмента
    elif action == "transfer":
        tool["responsible_id"] = user_id
        tool["responsible"] = user["name"]
        save_json(TOOLS_PATH, tools)
        await update.callback_query.edit_message_text(f"Инструмент {tool['name']} передан вам.")

    # Возврат на склад
    elif action == "store":
        tool["responsible_id"] = None
        tool["responsible"] = None
        tool["object"] = "Ladu"  # Если склад — это 'Ladu'
        save_json(TOOLS_PATH, tools)
        await update.callback_query.edit_message_text(f"Инструмент {tool['name']} возвращен на склад.")

    # Запрос на передачу
    elif action == "request":
        if responsible_id:
            responsible_user = next(u for u in users if u["id"] == responsible_id)
            await update.callback_query.edit_message_text(f"Вы запросили передачу инструмента {tool['name']} у {responsible_user['name']}.")
        else:
            await update.callback_query.edit_message_text(f"Инструмент {tool['name']} ещё не закреплен за кем-либо.")

# Хендлеры
from telegram.ext import CallbackQueryHandler, MessageHandler, filters

app.add_handler(CallbackQueryHandler(process_tool_id, pattern="^find_tool$"))  # Найти инструмент
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, process_tool_id))  # Поиск по ID