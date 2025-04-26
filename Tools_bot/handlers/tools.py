from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import os, json
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
TOOLS_PATH = os.path.join(DATA_DIR, "tools.json")
USERS_PATH = os.path.join(DATA_DIR, "users.json")
FOREMEN_PATH = os.path.join(DATA_DIR, "foremen.json")
PENDING_PATH = os.path.join(DATA_DIR, "pending.json")

def load_json(path):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def log_action(user_id, action, tool):
    log = load_json(PENDING_PATH)
    log.append({
        "timestamp": datetime.now().isoformat(),
        "user_id": user_id,
        "action": action,
        "tool_id": tool.get("id"),
        "tool_name": tool.get("name"),
        "object": tool.get("object"),
        "responsible": tool.get("responsible")
    })
    save_json(PENDING_PATH, log)

async def handle_tool_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    users = load_json(USERS_PATH)
    foremen = load_json(FOREMEN_PATH)
    tools = load_json(TOOLS_PATH)

    data = query.data
    action, tool_id = data.split(":")

    tool = next((t for t in tools if str(t["id"]) == tool_id), None)
    user = next((u for u in users if u["id"] == user_id), None)
    role = user.get("role", "Ответственный") if user else "Ответственный"

    if not tool:
        await query.edit_message_text("Инструмент не найден.")
        return

    if action == "take":
        tool["responsible"] = user["name"]
        tool["responsible_id"] = user_id
        save_json(TOOLS_PATH, tools)
        log_action(user_id, "Стал ответственным", tool)
        await query.edit_message_text(f"Вы стали ответственным за {tool['name']}.")

    elif action == "store":
        tool["responsible"] = None
        tool["responsible_id"] = None
        tool["object"] = "Ladu"
        save_json(TOOLS_PATH, tools)
        log_action(user_id, "Оставил на складе", tool)
        await query.edit_message_text(f"Инструмент {tool['name']} возвращен на склад.")

    elif action == "request":
        responsible_id = tool.get("responsible_id")
        if responsible_id:
            responsible_user = next((u for u in users if u["id"] == responsible_id), None)
            if responsible_user:
                await query.edit_message_text(f"Вы отправили запрос на передачу {tool['name']} у {responsible_user['name']}.")
        else:
            await query.edit_message_text("Инструмент не имеет текущего ответственного.")

    elif action == "transfer":
        # Показать список сотрудников
        buttons = []
        for person in foremen:
            if person["role"] == "Ответственный":
                buttons.append([
                    InlineKeyboardButton(person["name"], callback_data=f"confirm_transfer:{tool_id}:{person['name']}")
                ])
        await query.edit_message_text("Кому передать инструмент?", reply_markup=InlineKeyboardMarkup(buttons))

    elif action == "assign":
        # Список для назначения ответственным
        buttons = []
        for person in foremen:
            buttons.append([
                InlineKeyboardButton(person["name"], callback_data=f"confirm_assign:{tool_id}:{person['name']}")
            ])
        await query.edit_message_text("Кого назначить ответственным?", reply_markup=InlineKeyboardMarkup(buttons))

    elif action == "export":
        await query.edit_message_text("Функция экспорта в Excel скоро будет доступна.")

    # Подтверждение передачи
    elif action == "confirm_transfer":
        _, tool_id, target_name = data.split(":")
        tool = next((t for t in tools if str(t["id"]) == tool_id), None)
        new_resp = next((f for f in foremen if f["name"] == target_name), None)
        if tool and new_resp and "id" in new_resp:
            tool["responsible"] = new_resp["name"]
            tool["responsible_id"] = new_resp["id"]
            save_json(TOOLS_PATH, tools)
            log_action(user_id, f"Передал {tool['name']} → {target_name}", tool)
            await query.edit_message_text(f"Инструмент {tool['name']} передан {target_name}.")
        else:
            await query.edit_message_text("Не удалось передать инструмент.")

    # Подтверждение назначения
    elif action == "confirm_assign":
        _, tool_id, target_name = data.split(":")
        tool = next((t for t in tools if str(t["id"]) == tool_id), None)
        new_resp = next((f for f in foremen if f["name"] == target_name), None)
        if tool and new_resp and "id" in new_resp:
            tool["responsible"] = new_resp["name"]
            tool["responsible_id"] = new_resp["id"]
            save_json(TOOLS_PATH, tools)
            log_action(user_id, f"Назначил {target_name} ответственным", tool)
            await query.edit_message_text(f"{target_name} назначен ответственным за {tool['name']}.")
        else:
            await query.edit_message_text("Не удалось назначить ответственного.")
    pass
async def process_tool_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    await update.message.reply_text(f"Вы отправили ID инструмента: {user_message}")