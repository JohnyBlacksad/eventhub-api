"""Сервис пользователей.

Модуль содержит UserService для бизнес-логики пользователей:
регистрация, аутентификация, CRUD операции.
"""
import json
import hashlib
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException, status
from pydantic import BaseModel

from app.models.activation_code import ActivationCodeDAO
from app.models.events import EventDAO
from app.models.user import UserDAO
from app.schemas.enums.user_enums.users_status import UserRoleEnum
from app.schemas.users import GetUsersResponseModel, UserRegisterModel, UserResponseModel, UserUpdateModel
from app.services.auth import AuthService
from app.services.cache import CacheService, cache_service
from app.utils.logger import get_logger
from app.config_models.loggers_enum import LoggerName

logger = get_logger(LoggerName.USER_SERVICE_LOGGER)

class UserService:
    """Сервис для бизнес-логики пользователей.

    Использует UserDAO для CRUD операций и AuthService
    для работы с паролями.

    Атрибуты:
        user_dao: Data Access Object для пользователей.
        auth_service: Сервис аутентификации.
    """

    def __init__(
            self,
            user_dao: UserDAO,
            auth_service: AuthService,
            code_dao: ActivationCodeDAO,
            event_dao: EventDAO,
            cache: Optional[CacheService] = None):
        """Инициализация UserService.

        Args:
            user_dao: UserDAO для CRUD операций.
            auth_service: AuthService для хеширования паролей.
            code_dao: ActivationCodeDAO для операций смены роли.
            event_dao: EventDAO для операций регистрации и создания событий.
            cache: Сервис кэширования.
        """
        self.user_dao = user_dao
        self.auth_service = auth_service
        self.code_dao = code_dao
        self.event_dao = event_dao
        self.cache = cache or cache_service

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
            logger.warning("Registration failed: email already exists", extra={
                "email": user_data.email
            })
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="The users email address already exists."
            )

        hashed_password = await self.auth_service.hash_password(user_data.password.get_secret_value())

        user_dict = user_data.model_dump(exclude={"password"})
        user_dict["hashed_password"] = hashed_password
        user_dict["created_at"] = datetime.now(timezone.utc)

        user_dict["role"] = UserRoleEnum.USER.value

        user_id = await self.user_dao.create_user(user_dict)
        new_user = await self.user_dao.get_user_by_id(user_id)

        await self.cache.delete_user_list()

        logger.info("User registered successfully", extra={
            "user_id": str(user_id),
            "email": user_data.email,
        })

        return UserResponseModel.model_validate(new_user, from_attributes=True)

    async def get_users(
        self, skip: int = 0, limit: int = 100, filter_obj: Optional[dict] = None
    ) -> GetUsersResponseModel:
        """Получить список пользователей с пагинацией и фильтрами.

        Args:
            skip: Количество пропускаемых записей (для пагинации).
            limit: Максимальное количество записей (для пагинации).
            filter_obj: Словарь с фильтрами (role, is_banned, created_at, created_at_to).

        Returns:
            GetUsersResponseModel: Список пользователей с метаданными.
        """

        if filter_obj is not None and isinstance(filter_obj, BaseModel):
            filter_data = filter_obj.model_dump_json(by_alias=True)
        else:
            filter_data = filter_obj

        query_str = f'{skip}:{limit}:{json.dumps(filter_data, sort_keys=True) if filter_data else ""}'
        filters_hash = hashlib.md5(query_str.encode()).hexdigest()

        cached_users = await self.cache.get_user_list(filters_hash)

        if cached_users:
            return GetUsersResponseModel(
                users=[UserResponseModel.model_validate(u) for u in cached_users]
            )

        raw_users = await self.user_dao.get_users(skip=skip, limit=limit, filter_obj=filter_obj)

        users = [UserResponseModel.model_validate(user, from_attributes=True) for user in raw_users]

        await self.cache.set_user_list(filters_hash, users)

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
            logger.warning("Login failed: user not found", extra={"email": email})
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User does not exist")

        if user.get("is_banned"):
            logger.warning("Login attempt by banned user", extra={
                "email": email,
                "user_id": str(user.get("_id")),
            })
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is banned")

        is_valid = await self.auth_service.verify_password(password, user.get("hashed_password"))

        if not is_valid:
            logger.warning("Login failed: invalid password", extra={"email": email})
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email or password is incorrect")

        logger.info("User logged in successfully", extra={
            "user_id": str(user.get("_id")),
            "email": email,
        })

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
        cached_user = await self.cache.get_user(user_id)

        if cached_user:
            return UserResponseModel.model_validate(cached_user)

        user = await self.user_dao.get_user_by_id(user_id)

        if not user:
            logger.warning("Get user by ID: User ID is incorrect", extra={"user_id": str(user_id)})
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="The id is incorrect")

        response_model = UserResponseModel.model_validate(user, from_attributes=True)

        await self.cache.set_user(user_id, response_model)

        return response_model

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

        if "password" in data_dict:
            if user_data.password is not None:
                raw_password = user_data.password.get_secret_value()
                data_dict["hashed_password"] = await self.auth_service.hash_password(raw_password)
            del data_dict["password"]

        updated_user = await self.user_dao.update_user(user_id, data_dict)

        if not updated_user:
            logger.warning("Update user: User not found", extra={"user_id": str(user_id)})
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        await self.cache.delete_user(user_id)
        await self.cache.delete_user_list()

        logger.info("Update user successfully", extra={"user_id": str(user_id),})

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
            logger.warning("Delete user: User not found", extra={"user_id": str(user_id)})
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        if user.get("role") != "user":
            if await self.event_dao.has_active_events(user_id):
                logger.warning("Delete user: Cannot delete organizer with published events", extra={"user_id": str(user_id)})
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete organizer with published events"
                )

        await self.cache.delete_user(user_id)
        await self.cache.delete_user_list()

        logger.info("Delete user successfully", extra={"user_id": str(user_id),})

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

        user = await self.user_dao.get_user_by_id(user_id)

        if not user:
            logger.warning("Upgrade user role: User not found", extra={"user_id": str(user_id)})
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='User not found')

        code_data = await self.code_dao.use_code(code_str, user_id)

        if not code_data:
            logger.warning("Upgrade user role: Invalid or expired activation code", extra={"user_id": str(user_id)})
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid or expired activation code")

        new_role = code_data.get("role", "ORGANIZER")

        updated_user = await self.user_dao.update_user_role(user_id, new_role)

        await self.cache.delete_user(user_id)
        await self.cache.delete_user_list()

        logger.info("Upgrade user role successfully", extra={"user_id": str(user_id)})

        return UserResponseModel.model_validate(updated_user, from_attributes=True)

    async def set_ban_user(self, user_id: str, is_banned: bool) -> UserResponseModel:
        """Забанить или разбанить пользователя.

        Args:
            user_id: MongoDB ObjectId пользователя.
            is_banned: Флаг бана (True — забанить, False — разбанить).

        Returns:
            UserResponseModel: Обновлённые данные пользователя.
        """
        current_user = await self.user_dao.get_user_by_id(user_id)

        if not current_user:
            logger.warning("Set ban status user: User not found.", extra={"user_id": str(user_id), "is_banned": is_banned})
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

        logger.info("User ban status changed", extra={
            "user_id": user_id,
            "is_banned": is_banned,
            "action": "ban" if is_banned else "unban",
        })

        updated_user = await self.user_dao.set_ban_user(user_id=user_id, is_banned=is_banned)

        await self.cache.delete_user(user_id)
        await self.cache.delete_user_list()

        return UserResponseModel.model_validate(updated_user, from_attributes=True)

    async def delete_user_by_admin(self, user_id: str) -> bool:
        """Удалить пользователя по ID (только для ADMIN).

        Удаляет пользователя без проверки на активные события.
        Используется в админских endpoint'ах для cascade удаления.

        Args:
            user_id: MongoDB ObjectId пользователя.

        Returns:
            bool: True если пользователь удалён.

        Raises:
            HTTPException: 404 если пользователь не найден.
        """
        user = await self.user_dao.get_user_by_id(user_id)

        if not user:
            logger.warning("Delete user by admin: User not found.", extra={"user_id": str(user_id)})
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        result = await self.user_dao.delete_user(user_id)

        await self.cache.delete_user(user_id)
        await self.cache.delete_user_list()

        logger.info("Delete user by admin: Delete user successfully", extra={"user_id": user_id})

        return result

    async def change_user_role(self, user_id: str, new_role: UserRoleEnum) -> UserResponseModel:
        """Сменить роль пользователя (только ADMIN).

        Args:
            user_id: MongoDB ObjectId пользователя.
            new_role: Новая роль (user, organizer, admin).

        Returns:
            UserResponseModel: Обновлённые данные пользователя.
        """

        user = await self.user_dao.get_user_by_id(user_id)

        if not user:
            logger.warning("Change user role by admin: User not found.", extra={"user_id": str(user_id)})
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        updated_user = await self.user_dao.update_user_role(user_id, new_role)

        await self.cache.delete_user(user_id)
        await self.cache.delete_user_list()

        logger.info("Change user role by admin: Change user role successfully", extra={"user_id": user_id})

        return UserResponseModel.model_validate(updated_user, from_attributes=True)
