import os
import aiosqlite
from asyncio import Lock

DB_PATH = os.path.realpath(os.environ.get("DB_PATH", "data/hostio.db"))

MIGRATIONS = {
    1:
    """
    CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        name TEXT UNIQUE NOT NULL,
        path TEXT NOT NULL,
        status TEXT NOT NULL default 'not_built',
    )
    """,
}

class Database:
    def __init__(self):
        self.db_path = DB_PATH
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        self.connection = None
        self._lock = Lock()

    async def close(self):
        if type(self.connection) is not aiosqlite.Connection:
            raise ValueError("Database connection is not established")

        if self.connection:
            await self.connection.close()

    async def init(self):
        self.connection = await aiosqlite.connect(self.db_path)
        if type(self.connection) is not aiosqlite.Connection:
            raise ValueError("Database connection is not established")

        async with self.connection.cursor() as cursor:
            await cursor.execute("PRAGMA user_version")
            curr = await cursor.fetchone()
            current_version = curr[0] if curr else 0

            await cursor.execute("BEGIN")
            try:
                for version, migration in MIGRATIONS.items():
                    if not version > current_version:
                        continue
                    await cursor.execute(migration)
                    await cursor.execute(f"PRAGMA user_version = {version}")
            except Exception as e:
                await self.connection.rollback()
                raise e

            await self.connection.commit()

    async def initProject(self, name: str, path: str):
        if type(self.connection) is not aiosqlite.Connection:
            raise ValueError("Database connection is not established")

        async with self._lock:
            async with self.connection.cursor() as cursor:
                await cursor.execute(
                    "INSERT INTO projects (name, path) VALUES (?, ?)", (name, path)
                )
                await self.connection.commit()
