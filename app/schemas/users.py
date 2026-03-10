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

class UserRegisterModel(UserBaseModel):
    email: EmailStr # type: ignore[assignment]
    first_name: str = Field(..., min_length=2, alias='firstName') # type: ignore[assignment]
    last_name: str = Field(..., min_length=2, alias='lastName') # type: ignore[assignment]
    password: SecretStr = Field(..., min_length=8)

class UserLoginModel(BaseModel):
    email: EmailStr
    password: SecretStr

class UserResponseModel(UserBaseModel):
    id: PyObjectId = Field(alias='_id')
    email: EmailStr # type: ignore[assignment]
    first_name: str = Field(..., alias='firstName') # type: ignore[assignment]
    last_name: str = Field(..., alias='lastName') # type: ignore[assignment]
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserUpdateModel(UserBaseModel):
    password: Optional[SecretStr] = Field(None, min_length=8)

