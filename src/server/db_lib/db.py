import os
import aiosqlite

DB_PATH = os.path.realpath(os.environ.get("DB_PATH", "data/hostio.db"))

class Database:
    def __init__(self):
        self.db_path = DB_PATH
        os.makedirs(DB_PATH, exist_ok=True)
        self.connection = None

    async def connect(self):
        self.connection = await aiosqlite.connect(self.db_path)

    async def close(self):
        if self.connection:
            await self.connection.close()
