"""Подключение к MongoDB.

Модуль предоставляет класс EventDataBase для управления асинхронным
подключением к MongoDB через Motor драйвер.
"""

from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClient

from app.config import settings

from app.utils.logger import get_logger
from app.config_models.loggers_enum import LoggerName

logger = get_logger(LoggerName.DATA_BASE_LOGGER)

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
        logger.info("Connecting to MongoDB", extra={"uri": self._uri})
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
            await self.client.admin.command("ping")
            logger.debug("MongoDB ping successful")
        except Exception as e:
            logger.error("MongoDB ping failed", extra={"error": str(e)}, exc_info=True)
            raise ConnectionError(f"Database is not connected: {e}")


db_client = EventDataBase(uri=settings.mongo_db.url, db_name=settings.mongo_db.db_name)
