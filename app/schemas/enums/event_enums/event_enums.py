from enum import StrEnum

class EventStatusEnum(StrEnum):
    PUBLISHED = 'published'
    CANCELLED = 'cancelled'
    FINISHED = 'finished'

class RecurrenceEnum(StrEnum):
    NONE = 'none'
    DAILY = 'daily'
    WEEKLY = 'weekly'
    MONTHLY = 'monthly'
    YEARLY = 'yearly'