"""Модели событий.

Модуль содержит EventDAO для CRUD операций с событиями в MongoDB.
"""

from bson import ObjectId
from app.database import db_client
from motor.motor_asyncio import AsyncIOMotorCollection
from pymongo import ReturnDocument, ASCENDING, TEXT, DESCENDING


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
        - location.city + status (составной) — фильтрация по городу и статусу
        - deleted_at (TTL) — автоматическое удаление

        Args:
            collection: Коллекция MongoDB для событий.
        """
        await collection.create_index([("startDate", ASCENDING)])
        await collection.create_index([('title', TEXT)])
        await collection.create_index([('location.city', ASCENDING),
                                       ('status', ASCENDING)])
        await collection.create_index([('deleted_at', ASCENDING)], expireAfterSeconds=0)

    def __build_filter(self, filter_obj) -> dict:
        """Построить MongoDB query из объекта фильтров.

        Args:
            filter_obj: Объект фильтров (status, city, country, date_from, date_to, search).

        Returns:
            dict: Словарь с MongoDB query для фильтрации.
        """
        mongo_query = {}

        if not filter_obj:
            return mongo_query

        if getattr(filter_obj, 'status', None):
            mongo_query['status'] = filter_obj.status

        if getattr(filter_obj, 'city', None):
            mongo_query['location.city'] = filter_obj.city

        if getattr(filter_obj, 'country', None):
            mongo_query['location.country'] = filter_obj.country

        if getattr(filter_obj, 'date_from', None) or getattr(filter_obj, 'date_to', None):
            mongo_query['startDate'] = {}
            if filter_obj.date_from:
                mongo_query['startDate']['$gte'] = filter_obj.date_from
            if filter_obj.date_to:
                mongo_query['startDate']['$lte'] = filter_obj.date_to

        if getattr(filter_obj, 'search', None):
            mongo_query['$text'] = {'$search': filter_obj.search}

        return mongo_query

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
            filter_obj = None,  # type: ignore
            skip: int = 0,
            limit: int = 10,
            sort_by: str = 'startDate',
            sort_order: str = 'asc'
    ) -> list[dict]:
        """Получить список событий с пагинацией.

        Args:
            filter: Фильтр для поиска (опционально).
            skip: Количество пропускаемых записей.
            limit: Максимальное количество записей.

        Returns:
            Список документов событий.
        """
        query = self.__build_filter(filter_obj)

        direction = ASCENDING if sort_order == 'asc' else DESCENDING

        cursor = (self.collections
                  .find(query)
                  .sort(sort_by, direction)
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
            'status': {'$in': ['published']}
        }
        result = await self.collections.find_one(query)
        return result is not None