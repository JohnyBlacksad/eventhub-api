"""Схемы токенов.

Модуль содержит Pydantic схемы для JWT токенов:
access токен, refresh токен, данные токена.
"""

from pydantic import BaseModel, Field, ConfigDict, EmailStr
from app.schemas.users import PyObjectId


class TokenModel(BaseModel):
    """Схема ответа с парой токенов.

    Используется для ответа на /login и /register.

    Атрибуты:
        access_token: JWT access токен.
        refresh_token: JWT refresh токен.
        token_type: Тип токена (bearer).
    """
    model_config = ConfigDict(populate_by_name=True)
    access_token: str = Field(alias='accessToken')
    refresh_token: str = Field(alias='refreshToken')
    token_type: str = Field(default='bearer', alias='tokenType')


class TokenDataModel(BaseModel):
    """Данные внутри JWT токена.

    Используется для декодирования и валидации токена.

    Атрибуты:
        user_id: MongoDB ObjectId пользователя.
        email: Email адрес пользователя.
    """
    model_config = ConfigDict(populate_by_name=True)
    user_id: PyObjectId = Field(alias='userId')
    email: EmailStr