import aiosqlite
import asyncpg
import os

DATABASE_URL = os.getenv("DATABASE_URL")
LOCAL_DB = "database.db"

async def migrate_local_to_remote():
    print("Начинаем миграцию данных...")
    # Подключение к локальной базе
    async with aiosqlite.connect(LOCAL_DB) as local_db:
        # Подключение к удалённой базе
        remote_pool = await asyncpg.create_pool(DATABASE_URL)

        async with remote_pool.acquire() as remote_conn:
            # Перенос пользователей
            users = await local_db.execute_fetchall("SELECT id, name, role FROM users")
            for user in users:
                await remote_conn.execute("""
                    INSERT INTO users (id, name, role) VALUES ($1, $2, $3)
                    ON CONFLICT (id) DO NOTHING
                """, user[0], user[1], user[2])

            # Перенос инструментов
            tools = await local_db.execute_fetchall("SELECT id, name, object, responsible, responsible_id FROM tools")
            for tool in tools:
                await remote_conn.execute("""
                    INSERT INTO tools (id, name, object, responsible, responsible_id) VALUES ($1, $2, $3, $4, $5)
                    ON CONFLICT (id) DO NOTHING
                """, tool[0], tool[1], tool[2], tool[3], tool[4])

            # Перенос прорабов
            foremen = await local_db.execute_fetchall("SELECT id, name, role FROM foremen")
            for foreman in foremen:
                await remote_conn.execute("""
                    INSERT INTO foremen (id, name, role) VALUES ($1, $2, $3)
                    ON CONFLICT (id) DO NOTHING
                """, foreman[0], foreman[1], foreman[2])

            # Перенос истории
            pending = await local_db.execute_fetchall("SELECT timestamp, user_id, action, tool_id, tool_name, object, responsible FROM pending")
            for action in pending:
                await remote_conn.execute("""
                    INSERT INTO pending (timestamp, user_id, action, tool_id, tool_name, object, responsible)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                """, action[0], action[1], action[2], action[3], action[4], action[5], action[6])

    print("✅ Миграция завершена успешно!")