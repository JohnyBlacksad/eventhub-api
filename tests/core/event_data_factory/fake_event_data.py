"""Фабрика тестовых данных для событий.

Модуль содержит класс FakeEventData для генерации случайных
данных событий используя Faker.

Используется в тестах для создания реалистичных тестовых событий.
"""

import random
from datetime import datetime, timedelta, timezone
from typing import Optional

from faker import Faker
from mongomock import ObjectId

from app.schemas.enums.event_enums.event_enums import EventStatusEnum
from app.schemas.event import EventBaseModel, EventCreateModel


class FakeEventData:
    """Фабрика данных событий для тестов.

    Генерирует случайные но реалистичные данные событий:
    название, описание, местоположение, даты, статус.

    Attributes:
        faker: Faker instance для генерации данных.
    """

    def __init__(self, faker: Faker):
        """Инициализировать фабрику с Faker instance.

        Args:
            faker: Faker instance для генерации данных.
        """
        self.faker = faker

    def get_locations_dict(self, **kwargs):
        """Сгенерировать словарь местоположения события.

        Args:
            **kwargs: Дополнительные поля для переопределения.

        Returns:
            dict: Словарь с местоположением (country, city, address).
        """
        locations = {"country": self.faker.country(), "city": self.faker.city(), "address": self.faker.address()}
        locations.update(**kwargs)
        return locations

    def get_random_status(self, status: Optional[EventStatusEnum] = None):
        """Случайно выбрать статус события или вернуть указанный.

        Args:
            status: Опциональный статус для возврата.

        Returns:
            EventStatusEnum: Случайный или указанный статус.
        """
        status_list = [EventStatusEnum.CANCELLED, EventStatusEnum.FINISHED, EventStatusEnum.PUBLISHED]

        if not status:
            return random.choice(status_list)

        return status

    def generate_random_id(self):
        """Сгенерировать случайный ObjectId.

        Returns:
            str: Случайный ObjectId в виде строки.
        """
        return str(ObjectId())

    def get_event_data_dict(self, **kwargs) -> dict:
        """Сгенерировать словарь данных события.

        Args:
            **kwargs: Дополнительные поля для переопределения.

        Returns:
            dict: Словарь с данными события (title, description, location, dates, status, created_by).
        """
        event_data_dict = {
            "title": self.faker.text(max_nb_chars=15),
            "description": self.faker.text(max_nb_chars=150),
            "location": self.get_locations_dict(),
            "startDate": datetime.now(timezone.utc) + timedelta(days=15),
            "endDate": datetime.now(timezone.utc) + timedelta(days=30),
            "status": self.get_random_status(),
            "created_by": self.generate_random_id(),
            "created_at": datetime.now(timezone.utc),
        }

        event_data_dict.update(**kwargs)

        return event_data_dict

    def get_create_event_model(self):
        """Сгенерировать Pydantic модель события.

        Returns:
            EventCreateModel: Модель с случайными данными.
        """
        raw_data = self.get_event_data_dict()
        del raw_data['created_by']
        del raw_data['created_at']
        return EventCreateModel.model_validate(raw_data, from_attributes=True)


event_faker = FakeEventData(Faker("ru_RU"))
