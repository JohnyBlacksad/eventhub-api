from pydantic import BaseModel, Field, ConfigDict, EmailStr
from app.schemas.users import PyObjectId
from typing import Optional

class TokenModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    access_token: str = Field(alias='accessToken')
    refresh_token: str = Field(alias='refreshToken')
    token_type: str = Field(default='bearer', alias='tokenType')

class TokenDataModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    user_id: PyObjectId = Field(alias='userId')
    email: EmailStr