from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import os
import json
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
TOOLS_PATH = os.path.join(DATA_DIR, "tools.json")
USERS_PATH = os.path.join(DATA_DIR, "users.json")
PENDING_PATH = os.path.join(DATA_DIR, "pending.json")
FOREMEN_PATH = os.path.join(DATA_DIR, "foremen.json")

def load_json(path):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# Шаг 1. Пользователь нажал «Найти инструмент»
async def handle_tool_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.edit_message_text("Введи ID или название инструмента:")
    return

# Шаг 2. Обработка ввода ID или названия
async def process_tool_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text.strip()
    tools = load_json(TOOLS_PATH)

    # Поиск по ID (точное совпадение)
    tool = next((t for t in tools if str(t.get("id")) == query), None)

    if tool:
        await show_tool_card(update, context, tool)
        return

    # Если не найден — ищем по названию (нечувствительно к регистру, частичное совпадение)
    matches = [t for t in tools if query.lower() in t.get("name", "").lower()]
    
    if not matches:
        await update.message.reply_text("Инструмент не найден.")
        return
    elif len(matches) == 1:
        await show_tool_card(update, context, matches[0])
    else:
        text = f"Найдено {len(matches)} инструментов:"
        buttons = []
        for tool in matches:
            title = f"{tool.get('name')} (ID: {tool.get('id')})"
            buttons.append([InlineKeyboardButton(title, callback_data=f"view:{tool['id']}")])
        buttons.append([InlineKeyboardButton("◀️ Главное меню", callback_data="main_back")])
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons))

# Шаг 3. Отображение карточки инструмента
async def show_tool_card(update: Update, context: ContextTypes.DEFAULT_TYPE, tool: dict = None):
    if not tool:
        query = update.callback_query
        tool_id = query.data.split(":")[1]
        tools = load_json(TOOLS_PATH)
        tool = next((t for t in tools if str(t.get("id")) == tool_id), None)
        if not tool:
            await query.edit_message_text("Инструмент не найден.")
            return
        user_id = query.from_user.id
        respond_method = query.edit_message_text
    else:
        user_id = update.effective_user.id
        respond_method = update.message.reply_text

    users = load_json(USERS_PATH)
    user = next((u for u in users if u["id"] == user_id), None)
    role = user.get("role", "Ответственный") if user else "Ответственный"

    name = tool.get("name")
    tool_id = tool.get("id")
    object_ = tool.get("object", "—")
    responsible = tool.get("responsible") or "Никто"
    on_storage = "Да" if object_.lower() == "ladu" else "Нет"

    text = f"""**Инструмент:** {name}
    **ID:** {tool_id}
    **Объект:** {object_}
    **Ответственный:** {responsible}
    **На складе:** {on_storage}"""
    buttons = []

    # Кнопки по ролям
    if role == "Ответственный":
        if tool.get("responsible_id") is None:
            buttons.append([InlineKeyboardButton("✅ Стать ответственным", callback_data=f"take:{tool_id}")])
        elif tool.get("responsible_id") == user_id:
            buttons.append([
                InlineKeyboardButton("📤 Передать", callback_data=f"transfer:{tool_id}"),
                InlineKeyboardButton("🏬 Оставить на складе", callback_data=f"store:{tool_id}")
            ])
        else:
            buttons.append([InlineKeyboardButton("📥 Запросить передачу", callback_data=f"request:{tool_id}")])

    elif role in ["Супервайзер", "Шеф"]:
        buttons.append([InlineKeyboardButton("👤 Назначить ответственного", callback_data=f"assign:{tool_id}")])
        buttons.append([InlineKeyboardButton("🏬 Оставить на складе", callback_data=f"store:{tool_id}")])
        buttons.append([InlineKeyboardButton("🗂 История (Excel)", callback_data=f"export:{tool_id}")])

    buttons.append([InlineKeyboardButton("◀️ Главное меню", callback_data="main_back")])

    await respond_method(text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode="Markdown")

# Шаг 4. Действия логируются в pending.json
def log_action(user_id, action, tool):
    pending = load_json(PENDING_PATH)
    entry = {
        "timestamp": datetime.now().isoformat(),
        "user_id": user_id,
        "action": action,
        "tool_id": tool.get("id"),
        "tool_name": tool.get("name"),
        "responsible": tool.get("responsible"),
        "object": tool.get("object")
    }
    pending.append(entry)
    save_json(PENDING_PATH, pending)