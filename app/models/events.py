"""Модели событий.

Модуль содержит EventDAO для CRUD операций с событиями в MongoDB.
"""

from bson import ObjectId
from app.database import db_client
from motor.motor_asyncio import AsyncIOMotorCollection
from pymongo import ReturnDocument, ASCENDING, TEXT


class EventDAO:
    """Data Access Object для коллекции событий.

    Предоставляет методы для создания, чтения, обновления
    и удаления событий в MongoDB.

    Атрибуты:
        collections: Объект коллекции MongoDB для событий.
    """

    def __init__(self, collections: AsyncIOMotorCollection):
        """Инициализация EventDAO с коллекцией events."""
        self.collections = collections

    @classmethod
    async def setup_indexes(cls, collection: AsyncIOMotorCollection):
        """Создать индексы для коллекции событий.

        Создаёт индексы для:
        - startDate (ASCENDING) — сортировка по дате начала
        - title (TEXT) — полнотекстовый поиск
        - locations.city + status (составной) — фильтрация по городу и статусу
        - deleted_at (TTL) — автоматическое удаление

        Args:
            collection: Коллекция MongoDB для событий.
        """
        await collection.create_index([("startDate", ASCENDING)])
        await collection.create_index([('title', TEXT)])
        await collection.create_index([('locations.city', ASCENDING),
                                       ('status', ASCENDING)])
        await collection.create_index([('deleted_at', ASCENDING)], expireAfterSeconds=0)

    async def create_event(self, event_data: dict) -> str:
        """Создать новое событие в базе данных.

        Args:
            event_data: Словарь с данными события.

        Returns:
            ID созданного события в виде строки.
        """
        result = await self.collections.insert_one(event_data)
        return str(result.inserted_id)

    async def get_event(self, event_id: str) -> dict | None:
        """Найти событие по MongoDB ObjectId.

        Args:
            event_id: MongoDB ObjectId события в виде строки.

        Returns:
            Документ события в виде словаря, или None если не найден.
        """
        payload = {'_id': ObjectId(event_id)}
        result = await self.collections.find_one(payload)
        return result

    async def get_events(
            self,
            filter: dict = None,  # type: ignore
            skip: int = 0,
            limit: int = 10
    ) -> list[dict]:
        """Получить список событий с пагинацией.

        Args:
            filter: Фильтр для поиска (опционально).
            skip: Количество пропускаемых записей.
            limit: Максимальное количество записей.

        Returns:
            Список документов событий.
        """
        cursor = (self.collections
                  .find(filter or {})
                  .sort('startDate', ASCENDING)
                  .skip(skip)
                  .limit(limit)
                )

        return await cursor.to_list(length=limit)


    async def update_event(self, event_id: str, event_data: dict):
        """Обновить данные события по ID.

        Args:
            event_id: MongoDB ObjectId события в виде строки.
            event_data: Словарь с полями для обновления.

        Returns:
            Обновлённый документ события, или None если не найден.
        """
        payload = {'_id': ObjectId(event_id)}
        updated_event = await self.collections.find_one_and_update(
            payload,
            {'$set': event_data},
            return_document=ReturnDocument.AFTER
        )
        return updated_event

    async def delete_event(self, event_id: str):
        """Удалить событие по ID.

        Args:
            event_id: MongoDB ObjectId события в виде строки.

        Returns:
            True если событие удалено, False если не найдено.
        """
        payload = {'_id': ObjectId(event_id)}
        result = await self.collections.delete_one(payload)
        return result.deleted_count > 0

    async def has_active_events(self, user_id: str) -> bool:
        """Проверить, есть ли у пользователя активные события.

        Args:
            user_id: MongoDB ObjectId пользователя в виде строки.

        Returns:
            True если есть активные события, False иначе.
        """
        query = {
            'created_by': ObjectId(user_id),
            'status': {'$in': ['published', 'cancelled', 'finished']}
        }
        result = await self.collections.find_one(query)
        return result is not None