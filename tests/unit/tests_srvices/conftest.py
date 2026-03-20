"""Фикстуры для тестирования сервисов EventHub API.

Модуль содержит фикстуры для тестирования слоя сервисов:
- Auth сервис (JWT, bcrypt)
- User сервис (бизнес-логика пользователей)
- Event сервис (бизнес-логика событий)
- ActivationCode сервис (коды активации)
"""

import pytest

from app.config_models.auth_config import AuthConfig
from app.services.auth import AuthService
from tests.core.auth_data_factory.fake_auth_data import auth_faker
from tests.core.user_data_factory.fake_user_data import faker


@pytest.fixture
def mock_auth_settings():
    """Создать мок конфигурации JWT для тестов.

    Returns:
        AuthConfig: Конфигурация аутентификации для тестов.
    """
    auth_config = auth_faker.generate_auth_config_dict()
    return AuthConfig.model_validate(auth_config)


@pytest.fixture
def auth_service(mock_auth_settings: AuthConfig):
    """Создать AuthService с тестовой конфигурацией.

    Args:
        mock_auth_settings: Мок конфигурации JWT.

    Returns:
        AuthService: Сервис аутентификации для тестов.
    """
    return AuthService()


@pytest.fixture
def test_user_data():
    """Сгенерировать тестовые данные пользователя.

    Returns:
        dict: Словарь с данными пользователя (email, firstName, lastName, etc.).
    """
    fake_user = faker.get_user_register_data_dict()
    return fake_user


@pytest.fixture
async def valid_token(auth_service: AuthService, test_user_data: dict):
    """Создать валидный JWT токен для тестов.

    Args:
        auth_service: AuthService для создания токена.
        test_user_data: Данные пользователя для токена.

    Returns:
        str: JWT access токен.
    """
    return await auth_service.create_access_token(test_user_data)
