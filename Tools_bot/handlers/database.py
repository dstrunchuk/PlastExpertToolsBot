from supabase import create_client
import os

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

async def get_all_tools():
    data = supabase.table("tools").select("*").execute()
    return data.data

async def get_tool_by_id(tool_id):
    data = supabase.table("tools").select("*").eq("id", tool_id).single().execute()
    return data.data

async def add_tool(tool):
    supabase.table("tools").insert(tool).execute()

async def update_tool(tool):
    supabase.table("tools").update(tool).eq("id", tool["id"]).execute()

async def get_all_users():
    data = supabase.table("users").select("*").execute()
    return data.data

async def save_user(user):
    supabase.table("users").upsert(user).execute()

async def get_user_by_id(user_id):
    data = supabase.table("users").select("*").eq("id", user_id).single().execute()
    return data.data

async def get_all_foremen():
    data = supabase.table("foremen").select("*").execute()
    return data.data

async def add_foreman_if_missing(name, role, user_id):
    supabase.table("foremen").insert({
        "id": user_id,
        "name": name,
        "role": role
    }).execute()

async def update_foreman_id(name, user_id):
    supabase.table("foremen").update({"id": user_id}).eq("name", name).execute()

async def log_action(user_id, action, tool):
    supabase.table("pending").insert({
        "timestamp": tool.get("timestamp"),
        "user_id": user_id,
        "action": action,
        "tool_id": tool.get("id"),
        "tool_name": tool.get("name"),
        "object": tool.get("object"),
        "responsible": tool.get("responsible"),
    }).execute()

async def get_tool_history(tool_id):
    data = supabase.table("pending").select("*").eq("tool_id", tool_id).order("timestamp", desc=True).execute()
    return data.data