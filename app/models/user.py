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