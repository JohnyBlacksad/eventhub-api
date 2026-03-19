"""Модели конфигурации.

Модуль содержит Pydantic модели для настроек подключения к MongoDB.
"""

from pydantic import BaseModel


class MongoDBClient(BaseModel):
    """Настройки подключения к MongoDB.

    Атрибуты:
        url: URL подключения к MongoDB.
        db_name: Имя базы данных.
    """

    url: str
    db_name: str
