"""Модели конфигурации событий.

Модуль содержит Pydantic модели для настроек событий.
"""

from pydantic import BaseModel


class EventsConfig(BaseModel):
    """Настройки событий.

    Атрибуты:
        cleanup_sec: Время в секундах через которое события со статусом
            CANCELLED или FINISHED будут помечены на удаление.
    """

    cleanup_sec: int
