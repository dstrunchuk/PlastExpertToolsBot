import json
import os
import asyncio
import asyncpg
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

async def migrate():
    pool = await asyncpg.create_pool(DATABASE_URL)

    async with pool.acquire() as conn:
        # Foremen
        if os.path.exists("/mnt/data/foremen.json"):
            with open("/mnt/data/foremen.json", "r", encoding="utf-8") as f:
                foremen = json.load(f)
                for fman in foremen:
                    await conn.execute(
                        "INSERT INTO foremen (name, role, id) VALUES ($1, $2, $3) ON CONFLICT (name) DO NOTHING",
                        fman.get("name"), fman.get("role"), fman.get("id") or 0
                    )

        # Tools
        if os.path.exists("/mnt/data/tools.json"):
            with open("/mnt/data/tools.json", "r", encoding="utf-8") as f:
                tools = json.load(f)
                for tool in tools:
                    await conn.execute(
                        "INSERT INTO tools (id, name, object, responsible, responsible_id) VALUES ($1, $2, $3, $4, $5) ON CONFLICT (id) DO NOTHING",
                        str(tool["id"]), tool.get("name"), tool.get("object"), tool.get("responsible"), tool.get("responsible_id")
                    )

        # Users
        if os.path.exists("/mnt/data/users.json"):
            with open("/mnt/data/users.json", "r", encoding="utf-8") as f:
                users = json.load(f)
                for user in users:
                    await conn.execute(
                        "INSERT INTO users (id, name, role) VALUES ($1, $2, $3) ON CONFLICT (id) DO NOTHING",
                        user["id"], user["name"], user["role"]
                    )

        # Pending
        if os.path.exists("/mnt/data/pending.json"):
            with open("/mnt/data/pending.json", "r", encoding="utf-8") as f:
                pendings = json.load(f)
                for pending in pendings:
                    await conn.execute(
                        "INSERT INTO pending (timestamp, user_id, action, tool_id, tool_name, object, responsible) VALUES ($1, $2, $3, $4, $5, $6, $7)",
                        pending.get("timestamp"),
                        pending.get("user_id"),
                        pending.get("action"),
                        str(pending.get("tool_id")),
                        pending.get("tool_name"),
                        pending.get("object"),
                        pending.get("responsible")
                    )

    await pool.close()
    print("✅ Данные успешно перенесены!")

if __name__ == "__main__":
    asyncio.run(migrate())