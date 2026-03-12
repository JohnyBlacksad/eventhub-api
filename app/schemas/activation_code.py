from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime, timezone
from typing import Optional
from app.schemas.enums.user_enums.users_status import UserRoleEnum


class ActivationCodeBaseModel(BaseModel):
    code: str
    role: UserRoleEnum = UserRoleEnum.ORGANIZER

class ActivationCodeModelResponse(ActivationCodeBaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)
    id: str = Field(alias='_id')
    is_used: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    activated_at: Optional[datetime]