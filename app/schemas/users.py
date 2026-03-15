"""Схемы пользователей.

Модуль содержит Pydantic схемы для валидации данных пользователей:
регистрация, логин, профиль, обновление.
"""

from pydantic import (
    BaseModel,
    EmailStr,
    Field,
    ConfigDict,
    SecretStr,
    BeforeValidator)
from app.schemas.enums.user_enums.users_status import UserRoleEnum
from datetime import datetime, timezone
from typing import Annotated, Optional

PyObjectId = Annotated[str, BeforeValidator(str)]


class UserBaseModel(BaseModel):
    """Базовая модель пользователя.

    Используется как основа для других схем пользователей.
    Все поля кроме email опциональны.

    Атрибуты:
        email: Email адрес пользователя.
        first_name: Имя пользователя.
        last_name: Фамилия пользователя.
        phone_number: Номер телефона.
        role: Роль пользователя (user, admin, manager).
    """
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)
    email: Optional[EmailStr] = None
    first_name: Optional[str] = Field(
        default=None,
        min_length=2,
        alias='firstName'
    )
    last_name: Optional[str] = Field(
        default=None,
        min_length=2,
        alias='lastName'
    )
    phone_number: Optional[str] = Field(
        default=None,
        min_length=7,
        max_length=15,
        alias='phoneNumber'
    )
    role: Optional[UserRoleEnum] = UserRoleEnum.USER
    is_banned: Optional[bool] = Field(default=False, alias='isBanned')


class UserRegisterModel(UserBaseModel):
    """Схема для регистрации пользователя.

    Все поля обязательны. Email должен быть уникальным.
    """
    email: EmailStr                                                 # type: ignore
    first_name: str = Field(..., min_length=2, alias='firstName')   # type: ignore
    last_name: str = Field(..., min_length=2, alias='lastName')     # type: ignore
    password: SecretStr = Field(..., min_length=8)


class UserLoginModel(BaseModel):
    """Схема для входа пользователя.

    Атрибуты:
        email: Email адрес пользователя.
        password: Пароль пользователя.
    """
    email: EmailStr
    password: SecretStr


class UserResponseModel(UserBaseModel):
    """Схема для ответа API с данными пользователя.

    Атрибуты:
        id: MongoDB ObjectId пользователя.
        email: Email адрес пользователя.
        first_name: Имя пользователя.
        last_name: Фамилия пользователя.
        created_at: Дата и время создания аккаунта.
    """
    id: PyObjectId = Field(alias='_id')
    email: EmailStr                                                 # type: ignore
    first_name: Optional[str] = Field(default=None, alias='firstName')
    last_name: Optional[str] = Field(default=None, alias='lastName')
    created_at: datetime
    role: Optional[UserRoleEnum] = UserRoleEnum.USER
    is_banned: Optional[bool] = Field(default=False, alias='isBanned')


class UserUpdateModel(BaseModel):
    """Схема для обновления данных пользователя.

    Все поля опциональны. Обновляются только указанные поля.
    """
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)
    email: Optional[EmailStr] = Field(default=None)
    first_name: Optional[str] = Field(default=None, min_length=2, alias='firstName')
    last_name: Optional[str] = Field(default=None, min_length=2, alias='lastName')
    phone_number: Optional[str] = Field(default=None, min_length=7, max_length=15, alias='phoneNumber')
    password: Optional[SecretStr] = Field(None, min_length=8)

class GetUsersResponseModel(BaseModel):
    users: list[UserResponseModel]

class UserFilterModel(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True
    )

    role: Optional[str] = None
    is_banned: Optional[bool] = Field(default=None, alias='isBanned')
    created_at: Optional[datetime] = Field(default=None, alias='createdAt')
    created_at_to: Optional[datetime] = Field(default=None, alias='createdAtTo')
