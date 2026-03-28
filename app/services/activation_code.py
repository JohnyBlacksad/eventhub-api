"""Сервис кодов активации.

Модуль содержит ActivationCodeService для бизнес-логики кодов активации:
создание, получение, удаление кодов.
"""

from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from fastapi import HTTPException, status

from app.models.activation_code import ActivationCodeDAO
from app.schemas.activation_code import (
    ActivationCodeModelResponse,
    CodeFiltersResponse,
    GetActivationCodesResponseModel,
)
from app.schemas.enums.user_enums.users_status import UserRoleEnum
from app.utils.logger import get_logger
from app.config_models.loggers_enum import LoggerName


logger = get_logger(LoggerName.ACTIVATION_CODE_LOGGER)


class ActivationCodeService:
    """Сервис для бизнес-логики кодов активации.

    Использует ActivationCodeDAO для CRUD операций с кодами.

    Атрибуты:
        code_dao: Data Access Object для кодов активации.
    """

    def __init__(self, code_dao: ActivationCodeDAO):
        """Инициализация ActivationCodeService.

        Args:
            code_dao: ActivationCodeDAO для CRUD операций.
        """
        self.code_dao = code_dao

    async def __generate_code(self, role: UserRoleEnum) -> dict:
        """Сгенерировать случайный код активации.

        Args:
            role: Роль которую даёт код (ORGANIZER, ADMIN).

        Returns:
            dict: Словарь с данными кода (role, code).
        """
        code_data = {"role": role, "code": str(uuid4())}

        logger.info("Generating code successfully", extra={
            "role": role,
            "generated_at": datetime.now(timezone.utc)
        })

        return code_data

    async def create_code(
        self, role: UserRoleEnum = UserRoleEnum.ORGANIZER, code: Optional[str] = None
    ) -> ActivationCodeModelResponse:
        """Создать новый код активации.

        Args:
            role: Роль которую даёт код (ORGANIZER, ADMIN).
            code: Строка кода. Если None — сгенерируется автоматически.

        Returns:
            ActivationCodeModelResponse: Данные созданного кода.
        """
        if not code:
            code_data = await self.__generate_code(role)
        else:
            code_data = {"role": role, "code": code}

        code_id = await self.code_dao.create_code(code_data)
        created_code = await self.code_dao.get_code(code_id)
        created_code["_id"] = str(created_code["_id"])  # type: ignore

        logger.info("Creating code successfully", extra={
            "role": role,
            "code_id": str(code_id),
            "generated_at": datetime.now(timezone.utc)
        })

        return ActivationCodeModelResponse.model_validate(created_code)

    async def get_codes(
        self, skip: int = 0, limit: int = 100, filters: Optional[CodeFiltersResponse] = None
    ) -> GetActivationCodesResponseModel:
        """Получить список кодов активации с пагинацией и фильтрами.

        Args:
            skip: Количество пропускаемых записей.
            limit: Максимальное количество записей.
            filters: Фильтры для поиска (is_used, role, created_at, activated_at).

        Returns:
            GetActivationCodesResponseModel: Список кодов.
        """
        raw_list = await self.code_dao.get_codes(skip=skip, limit=limit, filters=filters)

        # Конвертируем ObjectId в строку для каждого кода
        codes = []
        for code in raw_list:
            code["_id"] = str(code["_id"])
            if code.get("activated_by"):
                code["activated_by"] = str(code["activated_by"])
            codes.append(ActivationCodeModelResponse.model_validate(code, from_attributes=True))

        return GetActivationCodesResponseModel(codes=codes)

    async def get_code(self, code_id: str) -> ActivationCodeModelResponse:
        """Получить код активации по ID.

        Args:
            code_id: MongoDB ObjectId кода.

        Returns:
            ActivationCodeModelResponse: Данные кода.

        Raises:
            HTTPException: 404 если код не найден.
        """
        response = await self.code_dao.get_code(code_id=code_id)

        if not response:
            logger.warning("Get code failed: Code not found", extra={
                "code_id": code_id,
            })
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Code not found")

        response["_id"] = str(response["_id"])
        if response.get("activated_by"):
            response["activated_by"] = str(response["activated_by"])
        return ActivationCodeModelResponse.model_validate(response, from_attributes=True)

    async def delete_code(self, code_id: str) -> bool:
        """Удалить код активации по ID.

        Args:
            code_id: MongoDB ObjectId кода.

        Returns:
            bool: True если код удалён.

        Raises:
            HTTPException: 404 если код не найден.
        """
        current_code = await self.code_dao.get_code(code_id)

        if not current_code:
            logger.warning("Delete code failed: Code not found", extra={
                "code_id": code_id,
            })
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Code not found")

        logger.info("Delete code successfully", extra={
                "code_id": code_id,
            })

        return await self.code_dao.delete_code(code_id)
