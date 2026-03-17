from typing import Optional

from faker import Faker
from datetime import datetime, timezone, timedelta

from mongomock import ObjectId
from app.schemas.enums.event_enums.event_enums import EventStatusEnum
import random

from app.schemas.event import EventBaseModel

class FakeEventData:
    def __init__(self, faker: Faker):
        self.faker = faker

    def get_locations_dict(self, **kwargs):
        locations = {
            'country': self.faker.country(),
            'city': self.faker.city(),
            'address': self.faker.address()
        }
        locations.update(**kwargs)
        return locations

    def get_random_status(self, status: Optional[EventStatusEnum] = None):
        status_list = [
            EventStatusEnum.CANCELLED,
            EventStatusEnum.FINISHED,
            EventStatusEnum.PUBLISHED
        ]

        if not status:
            return random.choice(status_list)

        return status

    def generate_random_id(self):
        return str(ObjectId())



    def get_event_data_dict(self, **kwargs) -> dict:
        event_data_dict = {
            'title': self.faker.text(max_nb_chars=15),
            'description': self.faker.text(max_nb_chars=150),
            'location': self.get_locations_dict(),
            'startDate': datetime.now(timezone.utc) + timedelta(days=15),
            'endDate': datetime.now(timezone.utc) + timedelta(days=30),
            'status': self.get_random_status(),
            'created_by': self.generate_random_id(),
            'created_at': datetime.now(timezone.utc)
        }

        event_data_dict.update(**kwargs)

        return event_data_dict

    def get_create_event_model(self):
        raw_data = self.get_event_data_dict()
        return EventBaseModel.model_validate(raw_data, from_attributes=True)

event_faker = FakeEventData(Faker('ru_RU'))