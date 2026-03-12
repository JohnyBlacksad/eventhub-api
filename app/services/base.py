"""Базовый сервис.

Модуль содержит базовый класс для сервисов с общими утилитами.
"""
from bson import ObjectId
from fastapi import HTTPException, status
from typing import TypeVar, Generic
from motor.motor_asyncio import AsyncIOMotorCollection

T = TypeVar('T')


class BaseService:
    """Базовый класс для сервисов.

    Предоставляет общие методы для проверки существования сущностей.
    """

    @staticmethod
    async def get_or_404(
        collection: AsyncIOMotorCollection,
        entity_id: str,
        entity_type: str = 'Entity'
    ) -> dict:
        """Получить сущность по ID или выбросить 404.

        Args:
            collection: MongoDB коллекция.
            entity_id: ObjectId сущности.
            entity_type: Тип сущности для сообщения об ошибке.

        Returns:
            dict: Документ сущности.

        Raises:
            HTTPException: 404 если сущность не найдена.
        """


        entity = await collection.find_one({'_id': ObjectId(entity_id)})

        if not entity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f'{entity_type} not found'
            )

        return entity


# Константы для пагинации
PAGINATION_DEFAULT_LIMIT = 10
PAGINATION_MAX_LIMIT = 100
PAGINATION_MIN_SKIP = 0

# Константы для событий
EVENT_TITLE_MIN_LENGTH = 3
EVENT_TITLE_MAX_LENGTH = 50
EVENT_DESCRIPTION_MIN_LENGTH = 15
EVENT_DESCRIPTION_MAX_LENGTH = 300

# Константы для регистраций
REGISTRATION_DEFAULT_LIMIT = 50
REGISTRATION_MAX_LIMIT = 1000

# Константы для пользователей
USER_PASSWORD_MIN_LENGTH = 8
USER_NAME_MIN_LENGTH = 2
USER_PHONE_MIN_LENGTH = 7
USER_PHONE_MAX_LENGTH = 15
