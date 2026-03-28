"""Модели кодов активации.

Модуль содержит ActivationCodeDAO для управления кодами
активации роли ORGANIZER.
"""

from datetime import datetime, timezone
from typing import Optional

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection
from pymongo import ReturnDocument

from app.schemas.activation_code import CodeFiltersResponse

from app.utils.logger import get_logger
from app.config_models.loggers_enum import LoggerName

logger = get_logger(LoggerName.ACTIVATION_CODE_DAO_LOGGER)

class ActivationCodeDAO:
    """Data Access Object для коллекции кодов активации.

    Предоставляет методы для создания, использования
    и удаления кодов активации.

    Атрибуты:
        collection: Объект коллекции MongoDB для кодов активации.
    """

    def __init__(self, collection: AsyncIOMotorCollection):
        """Инициализация ActivationCodeDAO с коллекцией org_code."""
        self.collection = collection

    @classmethod
    async def setup_indexes(cls, collection: AsyncIOMotorCollection):
        """Создать уникальный индекс на поле code.

        Args:
            collection: Коллекция MongoDB для кодов активации.
        """
        await collection.create_index([("code", 1)], unique=True)
        await collection.create_index([("activated_by", 1)])

    def __build_filter(self, filter_obj=None) -> dict:
        """Построить MongoDB query из объекта фильтров.

        Args:
            filter_obj: Объект фильтров (is_used, role, created_at, activated_at).

        Returns:
            dict: Словарь с MongoDB query для фильтрации.
        """
        mongo_query = {}

        if not filter_obj:
            return mongo_query

        if getattr(filter_obj, "is_used", None) is not None:
            mongo_query["is_used"] = filter_obj.is_used

        if getattr(filter_obj, "role", None):
            mongo_query["role"] = filter_obj.role

        if getattr(filter_obj, "created_at", None):
            mongo_query.setdefault("created_at", {})["$gte"] = filter_obj.created_at

        if getattr(filter_obj, "activated_at", None):
            mongo_query.setdefault("activated_at", {})["$gte"] = filter_obj.activated_at

        return mongo_query

    async def use_code(self, code_str: str, user_id: str) -> dict | None:
        """Использовать код активации (пометить как использованный).

        Args:
            code_str: Строка кода активации.

        Returns:
            Документ кода до обновления, или None если не найден.
        """
        try:
            code = {"code": code_str, "is_used": False}
            filter = {
                "$set": {"is_used": True, "activated_at": datetime.now(timezone.utc), "activated_by": ObjectId(user_id)}
            }
            result = await self.collection.find_one_and_update(code, filter, return_document=ReturnDocument.BEFORE)
            return result
        except Exception as e:
            logger.error("Use code error", extra={
                "user_id": user_id,
                "error": str(e)
            })
            raise

    async def create_code(self, code_data: dict) -> str:
        """Создать новый код активации.

        Args:
            code_data: Словарь с данными кода (code, role).

        Returns:
            ID созданного кода в виде строки.
        """
        try:
            code_data.update({"is_used": False, "created_at": datetime.now(timezone.utc)})
            result = await self.collection.insert_one(code_data)
            return str(result.inserted_id)
        except Exception as e:
            logger.error("Create code error", extra={
                "error": str(e),
            })
            raise

    async def delete_code(self, code_id: str) -> bool:
        """Удалить код активации по ID.

        Args:
            code_id: MongoDB ObjectId кода в виде строки.

        Returns:
            True если код удалён, False если не найден.
        """
        try:
            payload = {"_id": ObjectId(code_id)}
            result = await self.collection.delete_one(payload)
            return result.deleted_count > 0
        except Exception as e:
            logger.error("Delete code error", extra={
                "code_id": code_id,
                "error": str(e),
            })
            raise

    async def get_code(self, code_id: str) -> dict | None:
        """Получить код активации по ID.

        Args:
            code_id: MongoDB ObjectId кода в виде строки.

        Returns:
            dict | None: Документ кода в виде словаря, или None если не найден.
        """
        try:
            payload = {"_id": ObjectId(code_id)}
            result = await self.collection.find_one(payload)
            return result
        except Exception as e:
            logger.error("Get code error", extra={
                "code_id": code_id,
                "error": str(e),
            })
            raise

    async def get_codes(
        self, skip: int = 0, limit: int = 100, filters: Optional[CodeFiltersResponse] = None
    ) -> list[dict]:
        """Получить список кодов активации с пагинацией и фильтрами.

        Args:
            skip: Количество пропускаемых записей.
            limit: Максимальное количество записей.
            filters: Объект фильтров (is_used, role, created_at, activated_at).

        Returns:
            list[dict]: Список документов кодов.
        """
        query = self.__build_filter(filter_obj=filters)
        cursor = self.collection.find(query).sort("created_at", -1).skip(skip).limit(limit)

        return await cursor.to_list(length=limit)
