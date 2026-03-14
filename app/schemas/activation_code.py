from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime, timezone
from typing import Optional
from app.schemas.enums.user_enums.users_status import UserRoleEnum


class ActivationCodeBaseModel(BaseModel):
    code: str
    role: UserRoleEnum

class ActivationCodeCreateModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    role: UserRoleEnum
    code: Optional[str] = None

class ActivationCodeModelResponse(ActivationCodeBaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)
    id: str = Field(alias='_id')
    is_used: bool = Field(default=False, alias='isUsed')
    created_at: datetime = Field(alias='createdAt')
    activated_at: Optional[datetime] = Field(default=None, alias='activatedAt')
    activated_by: Optional[str] = Field(default=None, alias='activatedBy')

class GetActivationCodesResponseModel(BaseModel):
    codes: list[ActivationCodeModelResponse]

class CodeFiltersResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)
    is_used: Optional[bool] = Field(default=None, alias='isUsed')
    role: Optional[UserRoleEnum] = None
    created_at: Optional[datetime] = Field(default=None, alias='createdAt')
    activated_at: Optional[datetime] = Field(default=None, alias='activatedAt')