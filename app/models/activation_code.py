"""Модели кодов активации.

Модуль содержит ActivationCodeDAO для управления кодами
активации роли ORGANIZER.
"""

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection
from pymongo import ReturnDocument
from datetime import datetime, timezone


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
        await collection.create_index([('code', 1)], unique=True)

    async def use_code(self, code_str: str) -> dict | None:
        """Использовать код активации (пометить как использованный).

        Args:
            code_str: Строка кода активации.

        Returns:
            Документ кода до обновления, или None если не найден.
        """
        code = {'code': code_str, 'is_used': False}
        filter = {'$set': {'is_used': True, 'activated_at': datetime.now(timezone.utc)}}
        result = await self.collection.find_one_and_update(
            code,
            filter,
            return_document=ReturnDocument.BEFORE
        )
        return result

    async def create_code(self, code_data: dict) -> str:
        """Создать новый код активации.

        Args:
            code_data: Словарь с данными кода (code, role).

        Returns:
            ID созданного кода в виде строки.
        """
        code_data.update({
            'is_used': False,
            'created_at': datetime.now(timezone.utc)
        })
        result = await self.collection.insert_one(code_data)
        return str(result.inserted_id)

    async def delete_code(self, code_id: str) -> bool:
        """Удалить код активации по ID.

        Args:
            code_id: MongoDB ObjectId кода в виде строки.

        Returns:
            True если код удалён, False если не найден.
        """
        payload = {'_id': ObjectId(code_id)}
        result = await self.collection.delete_one(payload)
        return result.deleted_count > 0

    async def get_code(self, code_id: str):
        '''Получить один код по code id

        Args:
            code_id: MongoDB ObjectId кода в виде строки.

        Returns:
            Документ кода в виде словаря
        '''

        payload = {'_id': ObjectId(code_id)}
        result = await self.collection.find_one(payload)
        return result

    async def get_codes(self, skip: int = 0, limit: int = 100):
        '''Получить список всех кодов'''

        cursor = (self.collection.find()
                  .sort('created_at', -1)
                  .skip(skip)
                  .limit(limit))

        return await cursor.to_list(length=limit)

