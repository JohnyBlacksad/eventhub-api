"""Схемы событий.

Модуль содержит Pydantic схемы для валидации данных событий:
создание, обновление, ответ API.
"""

from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict, model_validator
from app.schemas.users import PyObjectId
from app.schemas.enums.event_enums.event_enums import EventStatusEnum, RecurrenceEnum


class EventLocationModel(BaseModel):
    """Местоположение события.

    Атрибуты:
        country: Страна проведения.
        city: Город проведения.
        address: Полный адрес.
        lat: Широта (опционально).
        lon: Долгота (опционально).
    """
    country: str
    city: str
    address: str
    lat: Optional[float] = None
    lon: Optional[float] = None


class EventBaseModel(BaseModel):
    """Базовая модель события.

    Используется как основа для других схем событий.

    Атрибуты:
        title: Название события (3-50 символов).
        description: Описание события (15-300 символов).
        location: Местоположение события.
        start_date: Дата и время начала.
        end_date: Дата и время окончания (опционально).
        max_participants: Максимальное количество участников (опционально).
        status: Статус события (published, cancelled, finished).
        recurrence: Тип повторения (none, daily, weekly, monthly, yearly).
    """
    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True
    )

    title: str = Field(min_length=3, max_length=50)
    description: str = Field(min_length=15, max_length=300)
    location: EventLocationModel
    start_date: datetime = Field(alias='startDate')
    end_date: Optional[datetime] = Field(default=None, alias='endDate')
    max_participants: Optional[int] = Field(default=None, alias='maxParticipants')
    status: EventStatusEnum = EventStatusEnum.PUBLISHED
    recurrence: RecurrenceEnum = RecurrenceEnum.NONE

    @model_validator(mode='after')
    def validate_dates(self) -> 'EventBaseModel':
        """Проверить, что end_date >= start_date.

        Returns:
            EventBaseModel: Текущий экземпляр если валидация пройдена.

        Raises:
            ValueError: Если end_date < start_date.
        """
        if self.end_date and self.end_date < self.start_date:
            raise ValueError('The end date of the event cannot be earlier than the start date.')
        return self


class EventCreateModel(EventBaseModel):
    """Схема для создания события.

    Все поля обязательны (наследуется от EventBaseModel).
    """
    pass


class EventUpdateModel(BaseModel):
    """Схема для обновления данных события.

    Все поля опциональны. Обновляются только указанные поля.

    Атрибуты:
        title: Название события (3-50 символов).
        description: Описание события (15-300 символов).
        location: Местоположение события.
        start_date: Дата и время начала.
        end_date: Дата и время окончания.
        max_participants: Максимальное количество участников.
        status: Статус события.
        recurrence: Тип повторения.
    """
    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True
    )

    title: Optional[str] = Field(default=None, min_length=3, max_length=50)
    description: Optional[str] = Field(default=None, min_length=15, max_length=300)
    location: Optional[EventLocationModel] = None
    start_date: Optional[datetime] = Field(default=None, alias='startDate')
    end_date: Optional[datetime] = Field(default=None, alias='endDate')
    max_participants: Optional[int] = Field(default=None, alias='maxParticipants')
    status: Optional[EventStatusEnum] = None
    recurrence: Optional[RecurrenceEnum] = None

    @model_validator(mode='after')
    def validate_dates(self) -> 'EventUpdateModel':

        if self.end_date and self.end_date < self.start_date:               # type: ignore
            raise ValueError('The end date of the event cannot be earlier than the start date.')
        return self


class EventResponseModel(EventBaseModel):
    """Схема для ответа API с данными события.

    Атрибуты:
        id: MongoDB ObjectId события.
        created_by: MongoDB ObjectId создателя события.
        created_at: Дата и время создания события.
    """
    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True
    )
    id: PyObjectId = Field(alias='_id')
    created_by: PyObjectId
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))