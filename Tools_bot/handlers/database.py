import asyncpg
import os
from datetime import datetime

DATABASE_URL = os.getenv("DATABASE_URL")

# Создание пула подключений
async def connect_db():
    pool = await asyncpg.create_pool(DATABASE_URL)
    return pool

# Получение всех инструментов
async def get_all_tools(pool):
    async with pool.acquire() as connection:
        rows = await connection.fetch(
            "SELECT id, name, object, responsible, responsible_id FROM tools"
        )
        return [dict(row) for row in rows]

# Получение всех пользователей
async def get_all_users(pool):
    async with pool.acquire() as connection:
        rows = await connection.fetch(
            "SELECT id, name, role FROM users"
        )
        return [dict(row) for row in rows]

# Получение всех прорабов
async def get_all_foremen(pool):
    async with pool.acquire() as connection:
        rows = await connection.fetch(
            "SELECT id, name, role FROM foremen"
        )
        return [dict(row) for row in rows]

# Получение одного инструмента по ID
async def get_tool_by_id(pool, tool_id):
    async with pool.acquire() as connection:
        row = await connection.fetchrow(
            "SELECT id, name, object, responsible, responsible_id FROM tools WHERE id = $1", tool_id
        )
        return dict(row) if row else None

# Добавление нового инструмента
async def add_tool(pool, tool):
    async with pool.acquire() as connection:
        await connection.execute(
            "INSERT INTO tools (id, name, object, responsible, responsible_id) VALUES ($1, $2, $3, $4, $5)",
            tool["id"], tool["name"], tool["object"], tool.get("responsible"), tool.get("responsible_id")
        )

# Обновление существующего инструмента
async def update_tool(pool, tool):
    async with pool.acquire() as connection:
        await connection.execute(
            "UPDATE tools SET name = $1, object = $2, responsible = $3, responsible_id = $4 WHERE id = $5",
            tool["name"], tool["object"], tool.get("responsible"), tool.get("responsible_id"), tool["id"]
        )

# Логирование действий с инструментами
async def log_action(pool, user_id, action, tool):
    async with pool.acquire() as connection:
        await connection.execute(
            """
            INSERT INTO pending (timestamp, user_id, action, tool_id, tool_name, object, responsible)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            """,
            datetime.now().isoformat(), user_id, action, tool.get("id"), tool.get("name"), tool.get("object"), tool.get("responsible")
        )

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
            """
            INSERT INTO users (id, name, role)
            VALUES ($1, $2, $3)
            ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, role = EXCLUDED.role
            """,
            user["id"], user["name"], user["role"]
        )

# Получение пользователя по ID
async def get_user_by_id(pool, user_id):
    async with pool.acquire() as connection:
        row = await connection.fetchrow(
            "SELECT id, name, role FROM users WHERE id = $1", user_id
        )
        return dict(row) if row else None

# Обновление ID прораба
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