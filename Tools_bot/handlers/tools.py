from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
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
    
    if action == "take":
        if responsible_id is None:
            # Стать ответственным за инструмент
            tool["responsible_id"] = user_id
            tool["responsible"] = user["name"]
            save_json(TOOLS_PATH, tools)
            await query.edit_message_text(f"Теперь вы ответственны за {tool['name']}.")
        else:
            await query.edit_message_text(f"Инструмент уже закреплен за {tool['responsible']}.")
    
    elif action == "transfer":
        if responsible_id is None:
            await query.edit_message_text(f"Инструмент {tool['name']} ещё не имеет ответственного.")
        else:
            # Передать инструмент
            tool["responsible_id"] = user_id
            tool["responsible"] = user["name"]
            save_json(TOOLS_PATH, tools)
            await query.edit_message_text(f"Инструмент {tool['name']} передан вам.")
    
    elif action == "store":
        # Вернуть на склад
        tool["responsible_id"] = None
        tool["responsible"] = None
        tool["object"] = "Ladu"  # Если склад — это 'Ladu'
        save_json(TOOLS_PATH, tools)
        await query.edit_message_text(f"Инструмент {tool['name']} возвращен на склад.")
    
    elif action == "request":
        if responsible_id:
            responsible_user = next(u for u in users if u["id"] == responsible_id)
            await query.edit_message_text(f"Вы запросили передачу инструмента {tool['name']} у {responsible_user['name']}.")
        else:
            await query.edit_message_text(f"Инструмент {tool['name']} ещё не закреплен за кем-либо.")

async def process_tool_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    tool_id = update.message.text.strip()

    tools = load_json(TOOLS_PATH)
    users = load_json(USERS_PATH)
    user = next((u for u in users if u["id"] == user_id), None)
    role = user.get("role", "Ответственный") if user else "Ответственный"

    tool = next((t for t in tools if str(t.get("id")) == tool_id), None)

    if not tool:
        await update.message.reply_text("Инструмент с таким ID не найден.")
        return

    responsible = tool.get("responsible")
    responsible_id = tool.get("responsible_id")
    obj = tool.get("object", "—")
    name = tool.get("name", "Без названия")

    text = f"*Инструмент:* {name}\n"
    text += f"*ID:* {tool.get('id')}\n"
    text += f"*Объект:* {obj}\n"
    text += f"*Ответственный:* {responsible or 'Никто'}"

    buttons = []

    if role in ["Супервайзер", "Шеф"]:
        buttons.append([InlineKeyboardButton("👤 Назначить ответственного", callback_data=f"assign:{tool_id}")])

    elif role == "Ответственный":
        if responsible_id is None:
            buttons.append([InlineKeyboardButton("✅ Стать ответственным", callback_data=f"take:{tool_id}")])
        elif responsible_id == user_id:
            buttons.append([
                InlineKeyboardButton("📤 Передать", callback_data=f"transfer:{tool_id}"),
                InlineKeyboardButton("🏬 Оставить на складе", callback_data=f"store:{tool_id}")
            ])
        else:
            buttons.append([InlineKeyboardButton("📥 Запросить передачу", callback_data=f"request:{tool_id}")])

    buttons.append([InlineKeyboardButton("◀️ Главная", callback_data="main_back")])

    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode=ParseMode.MARKDOWN
    )            