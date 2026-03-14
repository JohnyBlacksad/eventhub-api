"""Схемы кодов активации.

Модуль содержит Pydantic схемы для валидации данных кодов активации:
создание кода, ответ API, фильтры.
"""

from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime, timezone
from typing import Optional
from app.schemas.enums.user_enums.users_status import UserRoleEnum


class ActivationCodeBaseModel(BaseModel):
    """Базовая модель кода активации.

    Атрибуты:
        code: Строка кода.
        role: Роль которую даёт код (ORGANIZER, ADMIN).
    """
    code: str
    role: UserRoleEnum


class ActivationCodeCreateModel(BaseModel):
    """Схема для создания кода активации.

    Атрибуты:
        role: Роль которую даёт код (ORGANIZER, ADMIN).
        code: Строка кода. Если None — сгенерируется автоматически.
    """
    model_config = ConfigDict(populate_by_name=True)
    role: UserRoleEnum
    code: Optional[str] = None


class ActivationCodeModelResponse(ActivationCodeBaseModel):
    """Схема для ответа API с данными кода активации.

    Атрибуты:
        id: MongoDB ObjectId кода.
        is_used: Флаг использования кода.
        created_at: Дата и время создания кода.
        activated_at: Дата и время активации кода (опционально).
        activated_by: MongoDB ObjectId пользователя, активировавшего код.
    """
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)
    id: str = Field(alias='_id')
    is_used: bool = Field(default=False, alias='isUsed')
    created_at: datetime = Field(alias='createdAt')
    activated_at: Optional[datetime] = Field(default=None, alias='activatedAt')
    activated_by: Optional[str] = Field(default=None, alias='activatedBy')


class GetActivationCodesResponseModel(BaseModel):
    """Схема для ответа API со списком кодов активации.

    Атрибуты:
        codes: Список кодов активации.
    """
    codes: list[ActivationCodeModelResponse]


class CodeFiltersResponse(BaseModel):
    """Схема фильтров для поиска кодов активации.

    Атрибуты:
        is_used: Фильтр по флагу использования.
        role: Фильтр по роли.
        created_at: Фильтр по дате создания (от).
        activated_at: Фильтр по дате активации (от).
    """
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)
    is_used: Optional[bool] = Field(default=None, alias='isUsed')
    role: Optional[UserRoleEnum] = None
    created_at: Optional[datetime] = Field(default=None, alias='createdAt')
    activated_at: Optional[datetime] = Field(default=None, alias='activatedAt')