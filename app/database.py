from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional
from app.config import settings

class EventDataBase:
    def __init__(self, uri: str, db_name: str):
        self._uri = uri
        self._db_name = db_name
        self.client: Optional[AsyncIOMotorClient] = None
        self.db = None

    async def connect(self):
        self.client = AsyncIOMotorClient(self._uri)
        self.db = self.client[self._db_name]
        await self._ping()

    async def close(self):
        if self.client:
            self.client.close()

    def get_db(self):
        return self.db

    async def _ping(self):
        try:
            await self.client.admin.command('ping') # type: ignore
        except Exception as e:
            raise ConnectionError(f'Database is not connected: {e}')

db_client = EventDataBase(
    uri=settings.mongo_db.url,
    db_name=settings.mongo_db.db_name
)