import aiosqlite
import os
import json
from datetime import datetime

DB_PATH = "database.db"
DATABASE_URL = os.getenv("DATABASE_URL")

async def connect_db():
    pool = await asyncpg.create_pool(DATABASE_URL)
    return pool

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS tools (
                id TEXT PRIMARY KEY,
                name TEXT,
                object TEXT,
                responsible TEXT,
                responsible_id INTEGER
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                name TEXT,
                role TEXT
            )
        """)
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
        await db.execute("""
            CREATE TABLE IF NOT EXISTS foremen (
                id INTEGER,
                name TEXT,
                role TEXT
            )
        """)
        await db.commit()

async def get_all_tools():
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT id, name, object, responsible, responsible_id FROM tools")
        rows = await cursor.fetchall()
        return [dict(zip(["id", "name", "object", "responsible", "responsible_id"], row)) for row in rows]

async def get_tool_by_id(tool_id):
    async with aiosqlite.connect(DB_PATH) as db:
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

async def update_tool(tool):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE tools SET name = ?, object = ?, responsible = ?, responsible_id = ? WHERE id = ?",
            (tool["name"], tool["object"], tool.get("responsible"), tool.get("responsible_id"), tool["id"])
        )
        await db.commit()

async def get_all_users():
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT id, name, role FROM users")
        rows = await cursor.fetchall()
        return [dict(zip(["id", "name", "role"], row)) for row in rows]

async def save_user(user):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO users (id, name, role) VALUES (?, ?, ?)",
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

async def get_all_foremen():
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT id, name, role FROM foremen")
        rows = await cursor.fetchall()
        return [dict(zip(["id", "name", "role"], row)) for row in rows]

async def add_foreman_if_missing(name, role, user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO foremen (id, name, role) VALUES (?, ?, ?)",
            (user_id, name, role)
        )
        await db.commit()

async def update_foreman_id(name, user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE foremen SET id = ? WHERE name = ?",
            (user_id, name)
        )
        await db.commit()

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

async def get_tool_history(tool_id):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT timestamp, user_id, action, tool_name, object, responsible FROM pending WHERE tool_id = ? ORDER BY timestamp DESC",
            (tool_id,)
        )
        rows = await cursor.fetchall()
        return [dict(zip(["timestamp", "user_id", "action", "tool_name", "object", "responsible"], row)) for row in rows]