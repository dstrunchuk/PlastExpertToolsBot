import asyncio
import json
import os
from supabase import create_client, Client

# Настройки подключения к Supabase
SUPABASE_URL = "https://caqlqsumrhrgnpwzhdmo.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNhcWxxc3VtcmhyZ25wd3poZG1vIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDU2OTM1NDcsImV4cCI6MjA2MTI2OTU0N30.oXrQwJvXu9M9XoA4YXdkpH_8WTCW_tJno72izryevF4"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Пути до файлов
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
TOOLS_PATH = os.path.join(DATA_DIR, "tools.json")
USERS_PATH = os.path.join(DATA_DIR, "users.json")
FOREMEN_PATH = os.path.join(DATA_DIR, "foremen.json")
PENDING_PATH = os.path.join(DATA_DIR, "pending.json")

async def migrate_to_supabase():
    # Перенос инструментов
    if os.path.exists(TOOLS_PATH):
        with open(TOOLS_PATH, "r", encoding="utf-8") as f:
            tools = json.load(f)
            for tool in tools:
                supabase.table("tools").insert(tool).execute()
        print("✅ Tools перенесены!")

    # Перенос пользователей
    if os.path.exists(USERS_PATH):
        with open(USERS_PATH, "r", encoding="utf-8") as f:
            users = json.load(f)
            for user in users:
                supabase.table("users").insert(user).execute()
        print("✅ Users перенесены!")

    # Перенос прорабов
    if os.path.exists(FOREMEN_PATH):
        with open(FOREMEN_PATH, "r", encoding="utf-8") as f:
            foremen = json.load(f)
            for foreman in foremen:
                supabase.table("foremen").insert(foreman).execute()
        print("✅ Foremen перенесены!")

    # Перенос истории
    if os.path.exists(PENDING_PATH):
        with open(PENDING_PATH, "r", encoding="utf-8") as f:
            pending = json.load(f)
            for entry in pending:
                supabase.table("pending").insert(entry).execute()
        print("✅ Pending перенесены!")