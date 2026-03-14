from typing import Optional
from uuid import uuid4
from fastapi import HTTPException, status
from app.config import settings
from app.models.activation_code import ActivationCodeDAO
from app.schemas.activation_code import ActivationCodeModelResponse, CodeFiltersResponse, GetActivationCodesResponseModel
from app.schemas.enums.user_enums.users_status import UserRoleEnum

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

    async def get_codes(self, skip: int = 0, limit: int = 100, filters: Optional[CodeFiltersResponse] = None) -> GetActivationCodesResponseModel:
        raw_list = await self.code_dao.get_codes(
            skip=skip,
            limit=limit,
            filters=filters
        )

        codes = [ActivationCodeModelResponse.model_validate(code, from_attributes=True) for code in raw_list]

        return GetActivationCodesResponseModel(codes=codes)

    async def get_code(self, code_id: str) -> ActivationCodeModelResponse:
        response = await self.code_dao.get_code(code_id=code_id)

        if not response:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Code not found'
            )

        return ActivationCodeModelResponse.model_validate(response, from_attributes=True)

    async def delete_code(self, code_id: str) -> bool:
        current_code = await self.code_dao.get_code(code_id)

        if not current_code:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Code not found'
            )

        return await self.code_dao.delete_code(code_id)


