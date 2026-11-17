from pathlib import Path
import os
import aiosqlite

DB_PATH = Path(os.environ.get("DB_PATH", "data/hostio.db"))

class Database:
    def __init__(self):
        self.db_path = DB_PATH
        self.connection = None

    async def connect(self):
        self.connection = await aiosqlite.connect(self.db_path)

    async def close(self):
        if self.connection:
            await self.connection.close()
