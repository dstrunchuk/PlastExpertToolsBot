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

# Функция для логирования действия
async def log_action(entry):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO pending (timestamp, user_id, action, tool_id, tool_name, object, responsible) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (entry["timestamp"], entry["user_id"], entry["action"], entry["tool_id"], entry["tool_name"], entry["object"], entry["responsible"])
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
    async with aiosqlite.connect("database.db") as db:
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