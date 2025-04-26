import json
import os
import aiosqlite
from datetime import datetime

DB_PATH = "database.db"

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        # Таблица инструментов
        await db.execute("""
            CREATE TABLE IF NOT EXISTS tools (
                id TEXT PRIMARY KEY,
                name TEXT,
                object TEXT,
                responsible TEXT,
                responsible_id INTEGER
            )
        """)
        # Таблица пользователей
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                name TEXT,
                role TEXT
            )
        """)
        # Таблица истории действий
        await db.execute("""
            CREATE TABLE IF NOT EXISTS pending (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                user_id INTEGER,
                action TEXT,
                tool_id TEXT,
                tool_name TEXT,
                object TEXT,
                responsible TEXT
            )
        """)
        await db.commit()
        # Таблица прорабов
        await db.execute("""
            CREATE TABLE IF NOT EXISTS foremen (
                id INTEGER,
                name TEXT,
                role TEXT
            )
        """)
        await db.commit()

# Функция для получения всех инструментов
async def get_all_tools():
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT id, name, object, responsible, responsible_id FROM tools")
        rows = await cursor.fetchall()
        return [dict(zip(["id", "name", "object", "responsible", "responsible_id"], row)) for row in rows]

# Функция для получения всех пользователей
async def get_all_users():
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT id, name, role FROM users")
        rows = await cursor.fetchall()
        return [dict(zip(["id", "name", "role"], row)) for row in rows]

# Функция для добавления нового инструмента
async def add_tool(tool):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO tools (id, name, object, responsible, responsible_id) VALUES (?, ?, ?, ?, ?)",
            (tool["id"], tool["name"], tool["object"], tool.get("responsible"), tool.get("responsible_id"))
        )
        await db.commit()

# Функция для обновления инструмента
async def update_tool(tool):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE tools SET name = ?, object = ?, responsible = ?, responsible_id = ? WHERE id = ?",
            (tool["name"], tool["object"], tool.get("responsible"), tool.get("responsible_id"), tool["id"])
        )
        await db.commit()

# Функция для получения истории по инструменту
async def get_tool_history(tool_id):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT timestamp, user_id, action, tool_name, object, responsible FROM pending WHERE tool_id = ? ORDER BY timestamp DESC",
            (tool_id,)
        )
        rows = await cursor.fetchall()
        return [dict(zip(["timestamp", "user_id", "action", "tool_name", "object", "responsible"], row)) for row in rows]
    
import aiosqlite

async def get_all_foremen():
    async with aiosqlite.connect("database.db") as db:
        cursor = await db.execute("SELECT id, name, role FROM foremen")
        rows = await cursor.fetchall()
        result = []
        for row in rows:
            result.append({
                "id": row[0],
                "name": row[1],
                "role": row[2]
            })
        return result
    
async def get_tool_by_id(tool_id):
    async with aiosqlite.connect("database.db") as db:
        cursor = await db.execute("SELECT id, name, object, responsible, responsible_id FROM tools WHERE id = ?", (tool_id,))
        row = await cursor.fetchone()
        if row:
            return {
                "id": row[0],
                "name": row[1],
                "object": row[2],
                "responsible": row[3],
                "responsible_id": row[4]
            }
        return None
    
async def log_action(user_id, action, tool):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO pending (timestamp, user_id, action, tool_id, tool_name, object, responsible)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            user_id,
            action,
            tool.get("id"),
            tool.get("name"),
            tool.get("object"),
            tool.get("responsible")
        ))
        await db.commit()

async def save_user(user):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO users (id, name, role) VALUES (?, ?, ?)",
            (user["id"], user["name"], user["role"])
        )
        await db.commit()

async def get_user_by_id(user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT id, name, role FROM users WHERE id = ?", (user_id,))
        row = await cursor.fetchone()
        if row:
            return {"id": row[0], "name": row[1], "role": row[2]}
        return None

async def update_foreman_id(name, user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE foremen SET id = ? WHERE name = ?",
            (user_id, name)
        )
        await db.commit()

async def add_foreman_if_missing(name, role, user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO foremen (name, role, id) VALUES (?, ?, ?)",
            (name, role, user_id)
        )
        await db.commit()

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

USERS_PATH = os.path.join(DATA_DIR, "users.json")
TOOLS_PATH = os.path.join(DATA_DIR, "tools.json")
FOREMEN_PATH = os.path.join(DATA_DIR, "foremen.json")
PENDING_PATH = os.path.join(DATA_DIR, "pending.json")
DB_PATH = "database.db"

async def migrate_json_to_db():
    async with aiosqlite.connect(DB_PATH) as db:
        # Перенос users.json
        if os.path.exists(USERS_PATH):
            with open(USERS_PATH, "r", encoding="utf-8") as f:
                users = json.load(f)
                for user in users:
                    await db.execute(
                        "INSERT OR IGNORE INTO users (id, name, role) VALUES (?, ?, ?)",
                        (user["id"], user["name"], user["role"])
                    )

        # Перенос tools.json
        if os.path.exists(TOOLS_PATH):
            with open(TOOLS_PATH, "r", encoding="utf-8") as f:
                tools = json.load(f)
                for tool in tools:
                    await db.execute(
                        "INSERT OR IGNORE INTO tools (id, name, object, responsible, responsible_id) VALUES (?, ?, ?, ?, ?)",
                        (
                            str(tool["id"]),
                            tool.get("name", ""),
                            tool.get("object", ""),
                            tool.get("responsible"),
                            tool.get("responsible_id")
                        )
                    )

        # Перенос foremen.json
        if os.path.exists(FOREMEN_PATH):
            with open(FOREMEN_PATH, "r", encoding="utf-8") as f:
                foremen = json.load(f)
                for foreman in foremen:
                    await db.execute(
                        "INSERT OR IGNORE INTO foremen (id, name, role) VALUES (?, ?, ?)",
                        (
                            foreman.get("id", 0),  # если нет id, ставим 0, потом обновится
                            foreman["name"],
                            foreman["role"]
                        )
                    )

        # Перенос pending.json
        if os.path.exists(PENDING_PATH):
            with open(PENDING_PATH, "r", encoding="utf-8") as f:
                pending = json.load(f)
                for action in pending:
                    await db.execute(
                        "INSERT INTO pending (timestamp, user_id, action, tool_id, tool_name, object, responsible) VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (
                            action.get("timestamp", datetime.now().isoformat()),
                            action.get("user_id"),
                            action.get("action"),
                            str(action.get("tool_id")),
                            action.get("tool_name", ""),
                            action.get("object", ""),
                            action.get("responsible", "")
                        )
                    )

        await db.commit()
    print("✅ Миграция JSON в базу завершена.")

# Заливка начальных данных прорабов
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

async def seed_foremen():
    async with aiosqlite.connect(DB_PATH) as db:
        for foreman in INITIAL_FOREMEN:
            await db.execute(
                "INSERT OR IGNORE INTO foremen (id, name, role) VALUES (?, ?, ?)",
                (0, foreman["name"], foreman["role"])
            )
        await db.commit()
    print("✅ Прорабы успешно загружены в базу.")