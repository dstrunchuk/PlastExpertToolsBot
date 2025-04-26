import os
import json
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
USERS_PATH = os.path.join(DATA_DIR, "users.json")
TOOLS_PATH = os.path.join(DATA_DIR, "tools.json")
FOREMEN_PATH = os.path.join(DATA_DIR, "foremen.json")
PENDING_PATH = os.path.join(DATA_DIR, "pending.json")

INITIAL_FOREMEN = [
    {"name": "Sergei Strunchuk", "role": "Ответственный"},
    {"name": "Vladyslav Parkhomenko", "role": "Ответственный"},
    {"name": "Dmitri Kralya", "role": "Ответственный"},
    {"name": "Dmitri Karalko", "role": "Ответственный"},
    {"name": "Vitali Kulak", "role": "Ответственный"},
    {"name": "Oleh Kiekshyn", "role": "Ответственный"},
    {"name": "Aleksei Panin", "role": "Супервайзер"},
    {"name": "Shamil Kurbanov", "role": "Супервайзер"},
    {"name": "Juri Teras", "role": "Супервайзер"},
    {"name": "Alexei Dohin", "role": "Босс"}
]

async def init_db(pool):
    async with pool.acquire() as connection:
        await connection.execute("""
            CREATE TABLE IF NOT EXISTS tools (
                id TEXT PRIMARY KEY,
                name TEXT,
                object TEXT,
                responsible TEXT,
                responsible_id INTEGER
            )
        """)
        await connection.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id BIGINT PRIMARY KEY,
                name TEXT,
                role TEXT
            )
        """)
        await connection.execute("""
            CREATE TABLE IF NOT EXISTS pending (
                id SERIAL PRIMARY KEY,
                timestamp TEXT,
                user_id BIGINT,
                action TEXT,
                tool_id TEXT,
                tool_name TEXT,
                object TEXT,
                responsible TEXT
            )
        """)
        await connection.execute("""
            CREATE TABLE IF NOT EXISTS foremen (
                id BIGINT,
                name TEXT,
                role TEXT
            )
        """)
    print("✅ Таблицы проверены или созданы.")

async def migrate_json_to_db(pool):
    async with pool.acquire() as connection:
        # Перенос users.json
        if os.path.exists(USERS_PATH):
            with open(USERS_PATH, "r", encoding="utf-8") as f:
                users = json.load(f)
                for user in users:
                    await connection.execute(
                        "INSERT INTO users (id, name, role) VALUES ($1, $2, $3) ON CONFLICT (id) DO NOTHING",
                        user["id"], user["name"], user["role"]
                    )

        # Перенос tools.json
        if os.path.exists(TOOLS_PATH):
            with open(TOOLS_PATH, "r", encoding="utf-8") as f:
                tools = json.load(f)
                for tool in tools:
                    await connection.execute(
                        "INSERT INTO tools (id, name, object, responsible, responsible_id) VALUES ($1, $2, $3, $4, $5) ON CONFLICT (id) DO NOTHING",
                        str(tool["id"]),
                        tool.get("name", ""),
                        tool.get("object", ""),
                        tool.get("responsible"),
                        tool.get("responsible_id")
                    )

        # Перенос foremen.json
        if os.path.exists(FOREMEN_PATH):
            with open(FOREMEN_PATH, "r", encoding="utf-8") as f:
                foremen = json.load(f)
                for foreman in foremen:
                    await connection.execute(
                        "INSERT INTO foremen (id, name, role) VALUES ($1, $2, $3)",
                        foreman.get("id", 0),
                        foreman["name"],
                        foreman["role"]
                    )

        # Перенос pending.json
        if os.path.exists(PENDING_PATH):
            with open(PENDING_PATH, "r", encoding="utf-8") as f:
                pending = json.load(f)
                for action in pending:
                    await connection.execute(
                        "INSERT INTO pending (timestamp, user_id, action, tool_id, tool_name, object, responsible) VALUES ($1, $2, $3, $4, $5, $6, $7)",
                        action.get("timestamp", datetime.now().isoformat()),
                        action.get("user_id"),
                        action.get("action"),
                        str(action.get("tool_id")),
                        action.get("tool_name", ""),
                        action.get("object", ""),
                        action.get("responsible", "")
                    )
    print("✅ Миграция JSON в базу завершена.")

async def seed_foremen(pool):
    async with pool.acquire() as connection:
        for foreman in INITIAL_FOREMEN:
            await connection.execute(
                "INSERT INTO foremen (id, name, role) VALUES ($1, $2, $3)",
                0, foreman["name"], foreman["role"]
            )
    print("✅ Прорабы успешно добавлены в базу.")