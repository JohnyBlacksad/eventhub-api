from pydantic import BaseModel

class AuthConfig(BaseModel):
    crypto_schemas: str
    secret_key: str
    algorithm: str
    access_token_expire_time: int
    refresh_token_expire_time: int