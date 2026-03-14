from bson import ObjectId
from typing import Optional
from uuid import uuid4
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, status
from app.config import settings
from app.models.events import EventDAO
from app.models.activation_code import ActivationCodeDAO
from app.models.registration import RegistrationDAO
from app.schemas.activation_code import ActivationCodeCreateModel, ActivationCodeModelResponse
from app.schemas.enums.event_enums.event_enums import EventStatusEnum
from app.schemas.enums.user_enums.users_status import UserRoleEnum
from app.schemas.event import EventCreateModel, EventFilterParams, EventResponseModel, EventUpdateModel


class ActivationCodeService:
    def __init__(self, code_dao: ActivationCodeDAO):
        self.code_dao = code_dao

    async def __generate_code(self, role: UserRoleEnum):

        code_data = {
            'role': role,
            'code': str(uuid4())
        }

        return code_data

    async def create_code(self, role: UserRoleEnum = UserRoleEnum.ORGANIZER, code: Optional[str] = None) -> ActivationCodeModelResponse:

        if not code:
            code_data = await self.__generate_code(role)
        else:
            code_data = {'role': role, 'code': code}

        code_id = await self.code_dao.create_code(code_data)
        created_code = await self.code_dao.get_code(code_id)
        return ActivationCodeModelResponse.model_validate(created_code)