"""Сервис пользователей.

Модуль содержит UserService для бизнес-логики пользователей:
регистрация, аутентификация, CRUD операции.
"""

from fastapi import HTTPException, status
from datetime import datetime, timezone
from app.models.user import UserDAO
from app.services.auth import AuthService
from app.schemas.users import UserRegisterModel, UserResponseModel, UserUpdateModel


class UserService:
    """Сервис для бизнес-логики пользователей.

    Использует UserDAO для CRUD операций и AuthService
    для работы с паролями.

    Атрибуты:
        user_dao: Data Access Object для пользователей.
        auth_service: Сервис аутентификации.
    """

    def __init__(self, user_dao: UserDAO, auth_service: AuthService):
        """Инициализация UserService.

        Args:
            user_dao: UserDAO для CRUD операций.
            auth_service: AuthService для хеширования паролей.
        """
        self.user_dao = user_dao
        self.auth_service = auth_service

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
        return await self.user_dao.delete_user(user_id)