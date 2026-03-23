"""Схемы регистраций.

Модуль содержит Pydantic схемы для валидации данных регистраций.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.users import PyObjectId


class RegistrationResponseModel(BaseModel):
    """Схема для ответа API с данными регистрации.

    Атрибуты:
        id: MongoDB ObjectId регистрации.
        event_id: MongoDB ObjectId события.
        user_id: MongoDB ObjectId пользователя.
        registered_at: Дата и время регистрации.
    """

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    id: PyObjectId = Field(alias="_id")
    event_id: PyObjectId
    user_id: PyObjectId
    registered_at: datetime


class RegistrationCreateModel(BaseModel):
    """Схема для создания регистрации.

    Используется внутри сервиса (не в API).
    """

    event_id: str
    user_id: str
