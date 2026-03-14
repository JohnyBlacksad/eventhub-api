"""Сервис пользователей.

Модуль содержит UserService для бизнес-логики пользователей:
регистрация, аутентификация, CRUD операции.
"""

from typing import Optional

from fastapi import HTTPException, status
from datetime import datetime, timezone
from app.models.user import UserDAO
from app.models.activation_code import ActivationCodeDAO
from app.models.events import EventDAO
from app.services.auth import AuthService
from app.schemas.users import GetUsersResponseModel, UserRegisterModel, UserResponseModel, UserUpdateModel


class UserService:
    """Сервис для бизнес-логики пользователей.

    Использует UserDAO для CRUD операций и AuthService
    для работы с паролями.

    Атрибуты:
        user_dao: Data Access Object для пользователей.
        auth_service: Сервис аутентификации.
    """

    def __init__(self,
                 user_dao: UserDAO,
                 auth_service: AuthService,
                 code_dao:ActivationCodeDAO,
                 event_dao: EventDAO
                 ):
        """Инициализация UserService.

        Args:
            user_dao: UserDAO для CRUD операций.
            auth_service: AuthService для хеширования паролей.
        """
        self.user_dao = user_dao
        self.auth_service = auth_service
        self.code_dao = code_dao
        self.event_dao = event_dao

    async def register_user(self, user_data: UserRegisterModel) -> UserResponseModel:
        """Зарегистрировать нового пользователя.

        Args:
            user_data: Данные для регистрации.

        Returns:
            UserResponseModel: Данные созданного пользователя.

        Raises:
            HTTPException: 400 если email уже занят.
        """
        existing_user = await self.user_dao.get_user_by_email(user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='The users email address already exists.'
            )

        hashed_password = await self.auth_service.hash_password(
            user_data.password.get_secret_value()
        )

        user_dict = user_data.model_dump(exclude={'password'})
        user_dict['hashed_password'] = hashed_password
        user_dict['created_at'] = datetime.now(timezone.utc)

        user_id = await self.user_dao.create_user(user_dict)
        new_user = await self.user_dao.get_user_by_id(user_id)

        return UserResponseModel.model_validate(new_user, from_attributes=True)

    async def get_users(self, skip: int = 0, limit: int = 100, filter_obj: Optional[dict] = None) -> GetUsersResponseModel:
        raw_users = await self.user_dao.get_users(
            skip=skip,
            limit=limit,
            filter_obj=filter_obj
        )

        users = [UserResponseModel.model_validate(user, from_attributes=True) for user in raw_users]

        return GetUsersResponseModel(users=users)

    async def authenticate_user(self, email: str, password: str):
        """Аутентифицировать пользователя по email и паролю.

        Args:
            email: Email адрес пользователя.
            password: Пароль в открытом виде.

        Returns:
            dict: Документ пользователя из БД.

        Raises:
            HTTPException: 404 если пользователь не найден.
            HTTPException: 400 если пароль неверный.
        """
        user = await self.user_dao.get_user_by_email(email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='User does not exist'
            )

        if user.get('is_banned'):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='User is banned'
            )

        is_valid = await self.auth_service.verify_password(password, user.get('hashed_password'))

        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Email or password is incorrect'
            )

        return user

    async def get_user_by_id(self, user_id: str):
        """Получить пользователя по ID.

        Args:
            user_id: MongoDB ObjectId пользователя.

        Returns:
            UserResponseModel: Данные пользователя.

        Raises:
            HTTPException: 404 если пользователь не найден.
        """
        user = await self.user_dao.get_user_by_id(user_id)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='The id is incorrect'
            )

        return UserResponseModel.model_validate(user, from_attributes=True)

    async def update_user(self, user_id: str, user_data: UserUpdateModel):
        """Обновить данные пользователя.

        Args:
            user_id: MongoDB ObjectId пользователя.
            user_data: Данные для обновления.

        Returns:
            UserResponseModel: Обновлённые данные пользователя.

        Raises:
            HTTPException: 404 если пользователь не найден.
        """
        data_dict = user_data.model_dump(exclude_none=True)

        if 'password' in data_dict:
            if user_data.password is not None:
                raw_password = user_data.password.get_secret_value()
                data_dict['hashed_password'] = await self.auth_service.hash_password(raw_password)
            del data_dict['password']

        updated_user = await self.user_dao.update_user(user_id, data_dict)

        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='User not found'
            )

        return UserResponseModel.model_validate(updated_user, from_attributes=True)

    async def delete_user(self, user_id: str) -> bool:
        """Удалить пользователя по ID.

        Args:
            user_id: MongoDB ObjectId пользователя.

        Returns:
            bool: True если удалён, False если не найден.
        """
        user = await self.user_dao.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='User not found'
            )

        if user.get('role') != 'user':
            if await self.event_dao.has_active_events(user_id):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail='Cannot delete organizer with published events'
                )

        return await self.user_dao.delete_user(user_id)

    async def upgrade_role(self, user_id: str, code_str: str):
        """Повысить роль пользователя до ORGANIZER по коду активации.

        Проверяет код активации, помечает его как использованный
        и обновляет роль пользователя.

        Args:
            user_id: MongoDB ObjectId пользователя.
            code_str: Строка кода активации.

        Returns:
            UserResponseModel: Обновлённые данные пользователя.

        Raises:
            HTTPException: 403 если код невалиден или уже использован.
        """
        code_data = await self.code_dao.use_code(code_str, user_id)

        if not code_data:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='Invalid or expired activation code'
            )

        new_role = code_data.get('role', 'ORGANIZER')

        updated_user = await self.user_dao.update_user_role(user_id, new_role)

        return UserResponseModel.model_validate(updated_user, from_attributes=True)

    async def set_ban_user(self, user_id: str, is_banned: bool) -> UserResponseModel:
        current_user = await self.user_dao.get_user_by_id(user_id)

        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='User not found.'
            )

        updated_user = await self.user_dao.set_ban_user(
            user_id=user_id,
            is_banned=is_banned
        )

        return UserResponseModel.model_validate(updated_user, from_attributes=True)