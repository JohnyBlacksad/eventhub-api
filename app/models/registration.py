"""Модели регистраций.

Модуль содержит RegistrationDAO для операций с регистрациями
на события в MongoDB.
"""

from bson import ObjectId
from pymongo import ReturnDocument
from motor.motor_asyncio import AsyncIOMotorCollection
from datetime import datetime, timezone
from pymongo import ReturnDocument, ASCENDING, TEXT


class RegistrationDAO:
    """Data Access Object для коллекции регистраций.

    Предоставляет методы для добавления, удаления
    и получения регистраций на события.

    Атрибуты:
        collection: Объект коллекции MongoDB для регистраций.
    """

    def __init__(self, collection: AsyncIOMotorCollection) -> None:
        """Инициализация RegistrationDAO с коллекцией registrations."""
        self.collection = collection

    @classmethod
    async def setup_indexes(cls, collection: AsyncIOMotorCollection):
        """Создать индексы для коллекции регистраций.

        Создаёт индексы для:
        - event_id + user_id (unique составной) — предотвращение дублей
        - user_id (ASCENDING) — быстрый поиск регистраций пользователя

        Args:
            collection: Коллекция MongoDB для регистраций.
        """
        await collection.create_index(
            [('event_id', 1),('user_id', 1)],
            unique=True
        )
        await collection.create_index([('user_id', 1)])

    async def add_registration(self, event_id: str, user_id: str):
        """Добавить регистрацию пользователя на событие.

        Args:
            event_id: MongoDB ObjectId события в виде строки.
            user_id: MongoDB ObjectId пользователя в виде строки.

        Returns:
            Результат операции вставки.
        """
        result = await self.collection.insert_one({
            'event_id': ObjectId(event_id),
            'user_id': ObjectId(user_id),
            'registered_at': datetime.now(timezone.utc)
        })
        return result

    async def remove_registration(self, event_id: str, user_id: str):
        """Удалить регистрацию пользователя с события.

        Args:
            event_id: MongoDB ObjectId события в виде строки.
            user_id: MongoDB ObjectId пользователя в виде строки.

        Returns:
            Результат операции удаления.
        """
        result = await self.collection.delete_one({
            'event_id': ObjectId(event_id),
            'user_id': ObjectId(user_id)
        })
        return result

    async def get_event_registrations(
            self,
            event_id: str, skip: int = 0,
            limit: int = 50
    ) -> list[dict]:
        """Получить список регистраций на событие с пагинацией.

        Args:
            event_id: MongoDB ObjectId события в виде строки.
            skip: Количество пропускаемых записей.
            limit: Максимальное количество записей.

        Returns:
            Список документов регистраций.
        """
        cursor = (
            self.collection
            .find({'event_id': ObjectId(event_id)})
            .sort('registered_at', ASCENDING)
            .skip(skip)
            .limit(limit)
        )

        result = await cursor.to_list(length=limit)
        return result

    async def get_user_registartions(self, user_id: str) -> list[dict]:
        """Получить список регистраций пользователя.

        Args:
            user_id: MongoDB ObjectId пользователя в виде строки.

        Returns:
            Список документов регистраций пользователя.
        """
        cursor = self.collection.find({'user_id': ObjectId(user_id)})
        result = await cursor.to_list(length=100)
        return result