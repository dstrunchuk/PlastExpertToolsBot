import os
from datetime import datetime
from supabase import create_client, Client

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


# Получение всех инструментов
def get_all_tools():
    print("[DB] get_all_tools вызван")
    try:
        response = supabase.table("tools").select("*").execute()
        tools = response.data or []
        print(f"[DB] Получено инструментов: {len(tools)}")
        print(f"[DB] Ответ от Supabase: {response.data}")
        return tools
    except Exception as e:
        print(f"[!] Ошибка в get_all_tools: {e}")
        return []

# Получение одного инструмента по ID
def get_tool_by_id(tool_id):
    response = supabase.table("tools").select("*").eq("id", tool_id).maybe_single().execute()
    return response.data if response.data else None

# Добавление нового инструмента
def add_tool(tool):
    supabase.table("tools").insert(tool).execute()

# Обновление существующего инструмента
def update_tool(tool):
    try:
        if tool.get("id"):
            response = supabase.table("tools").update({
                "responsible_id": tool["responsible_id"]
            }).eq("id", tool["id"]).execute()
            context = f"по ID {tool['id']}"
        else:
            response = supabase.table("tools").update({
                "responsible_id": tool["responsible_id"]
            }).eq("name", tool["name"]).execute()
            context = f"по имени '{tool['name']}'"

        if response.data:
            print(f"Обновлён инструмент {context}: {response.data}")
        else:
            print(f"[!] Ничего не обновилось для инструмента {context}")
    except Exception as e:
        print(f"[Ошибка Supabase при обновлении инструмента] {e}")

# Получение всех пользователей
def get_all_users():
    response = supabase.table("users").select("*").execute()
    return response.data if response.data else []

# Сохранение пользователя (добавление или обновление)
def save_user(user):
    supabase.table("users").upsert(user).execute()

# Получение пользователя по ID
def get_user_by_id(user_id):
    response = supabase.table("users").select("*").eq("id", user_id).maybe_single().execute()
    if response and hasattr(response, "data") and response.data:
        return response.data
    else:
        return None

# Получение всех прорабов
def get_all_foremen():
    print("[DB] get_all_foremen вызван")
    try:
        response = supabase.table("foremen").select("*").execute()
        data = response.data or []
        print(f"[DB] Получено foremen: {len(data)}")
        return data
    except Exception as e:
        print(f"[!] Ошибка в get_all_foremen: {e}")
        return []

# Добавление нового прораба
def add_foreman_if_missing(name, role, user_id):
    supabase.table("foremen").insert({
        "id": user_id,
        "name": name,
        "role": role
    }).execute()

# Обновление ID у прораба
def update_foreman_id(name, user_id):
    print(f"[DB] Обновляю foremen — name: {name}, user_id: {user_id}")
    response = supabase.table("foremen").update({"id": user_id}).eq("name", name).execute()
    print(f"[DB] Ответ от Supabase: {response.data}")

# Логирование действий с инструментом
def log_action(user_id, action, tool):
    supabase.table("pending").insert({
        "timestamp": datetime.now().isoformat(),
        "user_id": user_id,
        "action": action,
        "tool_id": tool.get("id"),
        "tool_name": tool.get("name"),
        "object": tool.get("object"),
        "responsible": tool.get("responsible"),
    }).execute()

# Получение истории действий по инструменту
def get_tool_history(tool_id):
    response = supabase.table("pending").select("*").eq("tool_id", tool_id).order("timestamp", desc=True).execute()
    return response.data if response.data else []

# Создание пустого пользователя (если требуется)
def create_user(user_id, user_name):
    supabase.table("users").insert({
        "id": user_id,
        "name": user_name,
        "role": "Ответственный"
    }).execute()