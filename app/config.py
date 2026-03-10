from pydantic_settings import BaseSettings, SettingsConfigDict
from app.config_models.data_base_config import MongoDBClient

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        extra='allow',
        env_file='.env',
        env_file_encoding='utf-8',
        env_nested_delimiter='.',
    )

    mongo_db: MongoDBClient


settings = Settings()