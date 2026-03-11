from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict, model_validator
from app.schemas.users import PyObjectId
from app.schemas.enums.event_enums.event_enums import EventStatusEnum, RecurrenceEnum

class EventLocationModel(BaseModel):
    country: str
    city: str
    address: str
    lat: Optional[float] = None
    lon: Optional[float] = None

class EventBaseModel(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True
    )

    title: str = Field(min_length=3, max_length=50)
    descriptions: str = Field(min_length=15, max_length=300)
    locations: EventLocationModel
    start_date: datetime = Field(alias='startDate')
    end_date: Optional[datetime] = Field(default=None, alias='endDate')
    max_participants: Optional[int] = Field(default=None, alias='maxParticipants')
    status: EventStatusEnum = EventStatusEnum.PUBLISHED
    recurrence: RecurrenceEnum = RecurrenceEnum.NONE

    @model_validator(mode='after')
    def validate_dates(self) -> 'EventBaseModel':
        if self.end_date and self.end_date < self.start_date:
            raise ValueError('The end date of the event cannot be earlier than the start date.')
        return self


class EventCreateModel(EventBaseModel):
    pass

class EventUpdateModel(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True
    )

    title: Optional[str] = Field(default=None, min_length=3, max_length=50)
    descriptions: Optional[str] = Field(default=None, min_length=15, max_length=300)
    locations: Optional[EventLocationModel] = None
    start_date: Optional[datetime] = Field(default=None, alias='startDate')
    end_date: Optional[datetime] = Field(default=None, alias='endDate')
    max_participants: Optional[int] = Field(default=None, alias='maxParticipants')
    status: Optional[EventStatusEnum] = None
    recurrence: Optional[RecurrenceEnum] = None

class EventResponseModel(EventBaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True
    )
    id: PyObjectId = Field(alias='_id')
    participants: list[PyObjectId] = []
    created_by: PyObjectId
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))