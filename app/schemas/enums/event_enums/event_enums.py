"""Перечисления событий.

Модуль содержит Enum для статусов событий и типов повторения.
"""

from enum import StrEnum


class EventStatusEnum(StrEnum):
    """Статусы событий.

    Значения:
        PUBLISHED: Событие опубликовано и доступно для регистрации.
        CANCELLED: Событие отменено организатором.
        FINISHED: Событие завершено.
    """
    PUBLISHED = 'published'
    CANCELLED = 'cancelled'
    FINISHED = 'finished'


class RecurrenceEnum(StrEnum):
    """Типы повторения событий.

    Значения:
        NONE: Без повторения.
        DAILY: Ежедневно.
        WEEKLY: Еженедельно.
        MONTHLY: Ежемесячно.
        YEARLY: Ежегодно.
    """
    NONE = 'none'
    DAILY = 'daily'
    WEEKLY = 'weekly'
    MONTHLY = 'monthly'
    YEARLY = 'yearly'