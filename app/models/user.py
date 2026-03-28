"""Модели пользователей.

Модуль содержит UserDAO для CRUD операций с пользователями в MongoDB.
"""

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection
from pymongo import ReturnDocument

from app.utils.logger import get_logger
from app.config_models.loggers_enum import LoggerName

logger = get_logger(LoggerName.USER_DAO_LOGGER)

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
        await instance.collection.create_index("email", unique=True)

    def __build_filter(self, filter_obj) -> dict:
        """Внутренний фильтр-маппер: Превращает объект фильтров в запрос к MongoDB.

        Args:
            filter_obj: Объект фильтров (role, is_banned, created_at, created_at_to).

        Returns:
            dict: Словарь с нормализованными данными для передачи в MongoDB.
        """
        mongo_query = {}

        if not filter_obj:
            return mongo_query

        if getattr(filter_obj, "role", None):
            mongo_query["role"] = filter_obj.role

        if getattr(filter_obj, "is_banned", None):
            mongo_query["is_banned"] = filter_obj.is_banned

        if getattr(filter_obj, "created_at", None):
            mongo_query.setdefault("created_at", {})["$gte"] = filter_obj.created_at

        if getattr(filter_obj, "created_at_to", None):
            mongo_query.setdefault("created_at", {})["$lte"] = filter_obj.created_at_to

        return mongo_query

    async def create_user(self, user_data: dict) -> str:
        """Создать нового пользователя в базе данных.

        Args:
            user_data: Словарь с данными пользователя.
                       Должен включать: email, first_name, last_name, password.

        Returns:
            ID созданного пользователя в виде строки.
        """
        try:
            result = await self.collection.insert_one(user_data)
            return str(result.inserted_id)
        except Exception as e:
            logger.error("Failed to create user", extra={
                "error": str(e),
                "email": user_data.get("email", None)
            })
            raise

    async def get_users(self, skip: int = 0, limit: int = 0, filter_obj=None) -> list[dict]:
        """Получить список пользователей с пагинацией и фильтрами.

        Args:
            skip: Количество пропускаемых записей.
            limit: Максимальное количество записей.
            filter_obj: Объект фильтров (role, is_banned, created_at, created_at_to).

        Returns:
            list[dict]: Список документов пользователей.
        """
        try:
            query = self.__build_filter(filter_obj)
            cursor = self.collection.find(query).skip(skip).limit(limit)

            return await cursor.to_list(length=limit)
        except Exception as e:
            logger.error("Failed to get users", extra={
                "error": str(e),
            })
            raise

    async def get_user_by_id(self, user_id: str):
        """Найти пользователя по MongoDB ObjectId.

        Args:
            user_id: MongoDB ObjectId пользователя в виде строки.

        Returns:
            Документ пользователя в виде словаря, или None если не найден.
        """
        query_filter = {"_id": ObjectId(user_id)}
        result = await self.collection.find_one(query_filter)
        return result

    async def get_user_by_email(self, email: str):
        """Найти пользователя по email.

        Args:
            email: Email адрес пользователя.

        Returns:
            Документ пользователя в виде словаря, или None если не найден.
        """
        query_filter = {"email": email}
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
        try:
            query_filter = {"_id": ObjectId(user_id)}
            updated_user = await self.collection.find_one_and_update(
                query_filter, {"$set": update_data}, return_document=ReturnDocument.AFTER
            )
            return updated_user
        except Exception as e:
            logger.error("Update user failed", extra={
                "user_id": user_id,
                "error": str(e),
            })
            raise

    async def delete_user(self, user_id: str):
        """Удалить пользователя по ID.

        Args:
            user_id: MongoDB ObjectId пользователя в виде строки.

        Returns:
            True если пользователь удалён, False если не найден.
        """
        query_filter = {"_id": ObjectId(user_id)}
        result = await self.collection.delete_one(query_filter)
        return result.deleted_count > 0

    async def update_user_role(self, user_id: str, new_role: str):
        """Обновить роль пользователя.

        Args:
            user_id: MongoDB ObjectId пользователя в виде строки.
            new_role: Новая роль пользователя (user, organizer, admin).

        Returns:
            Обновлённый документ пользователя.
        """
        try:
            result = await self.collection.find_one_and_update(
                {"_id": ObjectId(user_id)}, {"$set": {"role": new_role}}, return_document=ReturnDocument.AFTER
            )
            return result
        except Exception as e:
            logger.error("Update user role failed", extra={
                "user_id": user_id,
                "role": new_role,
                "error": str(e)
            })
            raise

    async def set_ban_user(self, user_id: str, is_banned: bool):
        """Установить статус бана пользователя.

        Args:
            user_id: MongoDB ObjectId пользователя в виде строки.
            is_banned: Флаг бана (True — забанен, False — разбанен).

        Returns:
            Обновлённый документ пользователя.
        """
        try:
            result = await self.collection.find_one_and_update(
                {"_id": ObjectId(user_id)}, {"$set": {"is_banned": is_banned}}, return_document=ReturnDocument.AFTER
            )

            return result
        except Exception as e:
            logger.error("Ban user error", extra={
                "user_id": user_id,
                "is_banned": is_banned,
                "error": str(e),
            })
            raise
