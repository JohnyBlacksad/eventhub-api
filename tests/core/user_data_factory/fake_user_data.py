"""Фабрика тестовых данных для пользователей.

Модуль содержит класс FakeUserData для генерации случайных
данных пользователей используя Faker.

Используется в тестах для создания реалистичных тестовых данных.
"""

import random

from bson import ObjectId
from faker import Faker

from app.schemas.enums.user_enums.users_status import UserRoleEnum
from app.schemas.users import UserRegisterModel


class FakeUserData:
    """Фабрика данных пользователей для тестов.

    Генерирует случайные но реалистичные данные пользователей:
    email, имя, фамилия, телефон, пароль.

    Attributes:
        faker: Faker instance для генерации данных (locale: ru_RU).
    """

    def __init__(self, faker: Faker):
        """Инициализировать фабрику с Faker instance.

        Args:
            faker: Faker instance для генерации данных.
        """
        self.faker = faker

    def get_user_register_data_dict(self, **kwargs) -> dict:
        """Сгенерировать словарь данных для регистрации пользователя.

        Args:
            **kwargs: Дополнительные поля для переопределения.

        Returns:
            dict: Словарь с данными пользователя (email, firstName, lastName, phoneNumber, password).
        """
        user_data = {
            "email": self.faker.email(domain="@test.com"),
            "firstName": self.faker.first_name(),
            "lastName": self.faker.last_name(),
            "phoneNumber": self.faker.phone_number(),
            "password": self.faker.password(length=12),
        }

        user_data.update(**kwargs)

        return user_data

    def get_user_register_model(self) -> UserRegisterModel:
        """Сгенерировать Pydantic модель для регистрации.

        Returns:
            UserRegisterModel: Модель с случайными данными.
        """
        user_reg = self.get_user_register_data_dict()
        return UserRegisterModel.model_validate(user_reg, from_attributes=True)

    def generate_user_id(self) -> str:
        """Сгенерировать случайный MongoDB ObjectId.

        Returns:
            str: Случайный ObjectId в виде строки.
        """
        random_id = str(ObjectId())
        return random_id

    def get_role(self) -> str:
        """Случайно выбрать роль (ADMIN или ORGANIZER).

        Returns:
            str: Случайная роль пользователя.
        """
        roles = [UserRoleEnum.ADMIN, UserRoleEnum.ORGANIZER]
        return random.choice(roles)


faker = FakeUserData(Faker("ru_RU"))
