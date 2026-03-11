"""Конфигурация приложения.

Модуль содержит класс Settings для загрузки переменных окружения
через pydantic-settings.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from app.config_models.data_base_config import MongoDBClient


class Settings(BaseSettings):
    """Настройки приложения.

    Загружает переменные окружения из .env файла.
    Вложенные настройки используют разделитель '.' (например, MONGO_DB.URL).

    Атрибуты:
        mongo_db: Настройки подключения к MongoDB.
    """

    model_config = SettingsConfigDict(
        extra='allow',
        env_file='.env',
        env_file_encoding='utf-8',
        env_nested_delimiter='.',
    )

    mongo_db: MongoDBClient


settings = Settings()