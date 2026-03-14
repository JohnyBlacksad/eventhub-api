"""Модели пользователей.

Модуль содержит UserDAO для CRUD операций с пользователями в MongoDB.
"""

from bson import ObjectId
from pymongo import ReturnDocument
from motor.motor_asyncio import AsyncIOMotorCollection

class UserDAO:
    """Data Access Object для коллекции пользователей.

    Предоставляет методы для создания, чтения, обновления
    и удаления пользователей в MongoDB.

    Атрибуты:
        collection: Объект коллекции MongoDB для пользователей.
    """

    def __init__(self, collection: AsyncIOMotorCollection):
        """Инициализация UserDAO с коллекцией users."""
        self.collection = collection

    @classmethod
    async def setup_indexes(cls, collection: AsyncIOMotorCollection):
        """Создать индексы для коллекции пользователей.

        Создаёт уникальный индекс на поле email для предотвращения
        дублирования пользователей.
        """
        instance = cls(collection)
        await instance.collection.create_index('email', unique=True)

    def __build_filter(self, filter_obj) -> dict:
        '''Внутренний фильтр-маппер: Превращает объект фильтров в запрос к MongoDB

        - filtr_obj: Объект фильтра

        returns:
            dict: Словарь с нормализованными данными для передачи в Mongo DB.
        '''
        mongo_query = {}

        if not filter_obj:
            return mongo_query

        if getattr(filter_obj, 'role', None):
            mongo_query['role'] = filter_obj.role

        if getattr(filter_obj, 'is_banned', None):
            mongo_query['is_banned'] = filter_obj.is_banned

        if getattr(filter_obj, 'created_at', None):
            mongo_query['created_at'] = {}
            mongo_query['created_at']['$gte'] = filter_obj.created_at

        return mongo_query

    async def create_user(self, user_data: dict) -> str:
        """Создать нового пользователя в базе данных.

        Args:
            user_data: Словарь с данными пользователя.
                       Должен включать: email, first_name, last_name, password.

        Returns:
            ID созданного пользователя в виде строки.
        """
        result = await self.collection.insert_one(user_data)
        return str(result.inserted_id)

    async def get_users(self, skip: int = 0, limit: int = 0, filter_obj = None) -> list[dict]:
        query = self.__build_filter(filter_obj)
        cursor = (self.collection
                  .find(query)
                  .skip(skip)
                  .limit(limit))

        return await cursor.to_list(length=limit)

    async def get_user_by_id(self, user_id: str):
        """Найти пользователя по MongoDB ObjectId.

        Args:
            user_id: MongoDB ObjectId пользователя в виде строки.

        Returns:
            Документ пользователя в виде словаря, или None если не найден.
        """
        query_filter = {'_id': ObjectId(user_id)}
        result = await self.collection.find_one(query_filter)
        return result

    async def get_user_by_email(self, email: str):
        """Найти пользователя по email.

        Args:
            email: Email адрес пользователя.

        Returns:
            Документ пользователя в виде словаря, или None если не найден.
        """
        query_filter = {'email': email}
        result = await self.collection.find_one(query_filter)
        return result

    async def update_user(self, user_id: str, update_data: dict):
        """Обновить данные пользователя по ID.

        Args:
            user_id: MongoDB ObjectId пользователя в виде строки.
            update_data: Словарь с полями для обновления.

        Returns:
            Обновлённый документ пользователя, или None если не найден.
        """
        query_filter = {'_id': ObjectId(user_id)}
        updated_user = await self.collection.find_one_and_update(
            query_filter,
            {'$set': update_data},
            return_document=ReturnDocument.AFTER)
        return updated_user

    async def delete_user(self, user_id: str):
        """Удалить пользователя по ID.

        Args:
            user_id: MongoDB ObjectId пользователя в виде строки.

        Returns:
            True если пользователь удалён, False если не найден.
        """
        query_filter = {'_id': ObjectId(user_id)}
        result = await self.collection.delete_one(query_filter)
        return result.deleted_count > 0

    async def update_user_role(self, user_id: str, new_role: str):
        result = await self.collection.find_one_and_update(
            {'_id': ObjectId(user_id)},
            {'$set': {'role': new_role}},
            return_document=ReturnDocument.AFTER
        )
        return result

    async def set_ban_user(self, user_id: str, is_banned: bool):

        result = await self.collection.find_one_and_update(
            {'_id': ObjectId(user_id)},
            {'$set': {'is_banned': is_banned}},
            return_document=ReturnDocument.AFTER
        )

        return result