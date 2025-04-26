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

# Прочие функции для работы с базой

# Получение одного инструмента по ID
async def get_tool_by_id(pool, tool_id):
    async with pool.acquire() as connection:
        row = await connection.fetchrow("SELECT id, name, object, responsible, responsible_id FROM tools WHERE id = $1", tool_id)
        return dict(row) if row else None

# Получение всех инструментов
async def get_all_tools(pool):
    async with pool.acquire() as connection:
        rows = await connection.fetch("SELECT id, name, object, responsible, responsible_id FROM tools")
        return [dict(row) for row in rows]

# Получение всех пользователей
async def get_all_users(pool):
    async with pool.acquire() as connection:
        rows = await connection.fetch("SELECT id, name, role FROM users")
        return [dict(row) for row in rows]

# Получение всех прорабов
async def get_all_foremen(pool):
    async with pool.acquire() as connection:
        rows = await connection.fetch("SELECT id, name, role FROM foremen")
        return [dict(row) for row in rows]

# Получение истории по инструменту
async def get_tool_history(pool, tool_id):
    async with pool.acquire() as connection:
        rows = await connection.fetch(
            "SELECT timestamp, user_id, action, tool_name, object, responsible FROM pending WHERE tool_id = $1 ORDER BY timestamp DESC",
            tool_id
        )
        return [dict(row) for row in rows]

# Сохранение или обновление пользователя
async def save_user(pool, user):
    async with pool.acquire() as connection:
        await connection.execute(
            "INSERT INTO users (id, name, role) VALUES ($1, $2, $3) ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, role = EXCLUDED.role",
            user["id"], user["name"], user["role"]
        )

# Получение пользователя по ID
async def get_user_by_id(pool, user_id):
    async with pool.acquire() as connection:
        row = await connection.fetchrow("SELECT id, name, role FROM users WHERE id = $1", user_id)
        return dict(row) if row else None

# Логирование действия
async def log_action(pool, user_id, action, tool):
    async with pool.acquire() as connection:
        await connection.execute(
            "INSERT INTO pending (timestamp, user_id, action, tool_id, tool_name, object, responsible) VALUES ($1, $2, $3, $4, $5, $6, $7)",
            datetime.now().isoformat(), user_id, action, tool.get("id"), tool.get("name"), tool.get("object"), tool.get("responsible")
        )

# Обновление инструмента
async def update_tool(pool, tool):
    async with pool.acquire() as connection:
        await connection.execute(
            "UPDATE tools SET name = $1, object = $2, responsible = $3, responsible_id = $4 WHERE id = $5",
            tool["name"], tool["object"], tool.get("responsible"), tool.get("responsible_id"), tool["id"]
        )

# Обновление ID у прораба
async def update_foreman_id(pool, name, user_id):
    async with pool.acquire() as connection:
        await connection.execute(
            "UPDATE foremen SET id = $1 WHERE name = $2",
            user_id, name
        )

# Добавление нового прораба
async def add_foreman_if_missing(pool, name, role, user_id):
    async with pool.acquire() as connection:
        await connection.execute(
            "INSERT INTO foremen (name, role, id) VALUES ($1, $2, $3)",
            name, role, user_id
        )