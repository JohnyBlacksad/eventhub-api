"""Подключение к MongoDB.

Модуль предоставляет класс EventDataBase для управления асинхронным
подключением к MongoDB через Motor драйвер.
"""

from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional
from app.config import settings


class EventDataBase:
    """Класс для управления подключением к MongoDB.

    Атрибуты:
        client: Асинхронный клиент MongoDB.
        db: Объект базы данных.
    """

    def __init__(self, uri: str, db_name: str):
        """Инициализация подключения к MongoDB.

        Args:
            uri: URL подключения к MongoDB.
            db_name: Имя базы данных.
        """
        self._uri = uri
        self._db_name = db_name
        self.client: Optional[AsyncIOMotorClient] = None
        self.db = None

    async def connect(self):
        """Установить подключение к MongoDB.

        Создаёт клиент и проверяет подключение через ping.
        """
        self.client = AsyncIOMotorClient(self._uri)
        self.db = self.client[self._db_name]
        await self._ping()

    async def close(self):
        """Закрыть подключение к MongoDB."""
        if self.client:
            self.client.close()

    def get_db(self):
        """Получить объект базы данных.

        Returns:
            Объект базы данных MongoDB.
        """
        return self.db

    async def _ping(self):
        """Проверить подключение к MongoDB.

        Raises:
            ConnectionError: Если подключение не удалось.
        """
        try:
            await self.client.admin.command('ping')
        except Exception as e:
            raise ConnectionError(f'Database is not connected: {e}')


db_client = EventDataBase(
    uri=settings.mongo_db.url,
    db_name=settings.mongo_db.db_name
)