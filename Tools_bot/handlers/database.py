from supabase import create_client, Client
import os
from datetime import datetime

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Получение всех инструментов
async def get_all_tools():
    response = supabase.table("tools").select("*").execute()
    return response.data if response.data else []

# Получение одного инструмента по ID
async def get_tool_by_id(tool_id):
    response = supabase.table("tools").select("*").eq("id", tool_id).maybe_single().execute()
    return response.data if response.data else None

# Добавление нового инструмента
async def add_tool(tool):
    supabase.table("tools").insert(tool).execute()

# Обновление существующего инструмента
async def update_tool(tool):
    supabase.table("tools").update({
        "responsible_id": tool["responsible_id"]
    }).eq("id", tool["id"]).execute()

# Получение всех пользователей
async def get_all_users():
    response = supabase.table("users").select("*").execute()
    return response.data if response.data else []

# Сохранение пользователя (добавление или обновление)
async def save_user(user):
    supabase.table("users").upsert(user).execute()

# Получение пользователя по ID
async def get_user_by_id(user_id):
    response = supabase.table("users").select("*").eq("id", user_id).maybe_single().execute()
    if response and hasattr(response, "data") and response.data:
        return response.data
    else:
        return None

# Получение всех прорабов
async def get_all_foremen():
    response = supabase.table("foremen").select("*").execute()
    return response.data if response.data else []

# Добавление нового прораба
async def add_foreman_if_missing(name, role, user_id):
    supabase.table("foremen").insert({
        "id": user_id,
        "name": name,
        "role": role
    }).execute()

# Обновление ID у прораба
async def update_foreman_id(name, user_id):
    supabase.table("foremen").update({"id": user_id}).eq("name", name).execute()

# Логирование действий с инструментом
async def log_action(user_id, action, tool):
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
async def get_tool_history(tool_id):
    response = supabase.table("pending").select("*").eq("tool_id", tool_id).order("timestamp", desc=True).execute()
    return response.data if response.data else []

# Создание пустого пользователя (если требуется)
async def create_user(user_id, user_name):
    supabase.table("users").insert({
        "id": user_id,
        "name": user_name,
        "role": "Ответственный"
    }).execute()