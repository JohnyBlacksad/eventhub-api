from pydantic import BaseModel

class RedisConfig(BaseModel):
    url: str
    db: int
    password: str
