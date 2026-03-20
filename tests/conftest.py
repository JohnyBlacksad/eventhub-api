"""Конфигурация pytest и хуки для проекта EventHub API.

Модуль содержит:
- Отключение автоматической конвертации маркеров в теги Allure
- Наследование маркеров с класса на методы
- Прикрепление данных пользователя/события к отчёту при ошибках
"""

import allure
import allure_pytest.utils as utils
from mongomock_motor import AsyncMongoMockCollection
import pytest
from allure_commons.types import AttachmentType

from app.models.activation_code import ActivationCodeDAO
from app.models.events import EventDAO
from app.models.registration import RegistrationDAO
from app.models.user import UserDAO
from tests.core.const.allure_labels import AllureLabelApplier
from tests.mock.mongo_mock import get_mongo_mock

applier = AllureLabelApplier(default_owner="artem")


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config):

    def disabled_should_convert_mark_to_tag(mark):
        return False

    utils.should_convert_mark_to_tag = disabled_should_convert_mark_to_tag

@pytest.hookimpl(tryfirst=True)
def pytest_runtest_setup(item):
    if hasattr(item, "cls") and item.cls:
        for marker in item.cls.pytestmark:
            if not item.get_closest_marker(marker.name):
                item.add_marker(marker)
    applier.apply(item)


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()

    if report.when == "call" and report.failed:
        if "user_data" in item.funcargs:
            allure.attach(
                str(item.funcargs["user_data"]), name="user_data_on_failure", attachment_type=AttachmentType.JSON
            )

        if "event_data" in item.funcargs:
            allure.attach(
                str(item.funcargs["event_data"]), name="event_data_on_failure", attachment_type=AttachmentType.JSON
            )


@pytest.fixture
def mongo_mock():
    """Создать мок базу данных MongoDB для тестов.

    Returns:
        MockEventDatabase: Мок база данных с коллекциями.
    """
    db = get_mongo_mock()
    return db


@pytest.fixture
def user_collections(mongo_mock):
    """Получить мок коллекцию пользователей.

    Args:
        mongo_mock: Мок база данных.

    Returns:
        AsyncMongoMockCollection: Коллекция users.
    """
    user_collection = mongo_mock.get_users_collection()
    return user_collection


@pytest.fixture
def mock_user_dao(user_collections: AsyncMongoMockCollection):
    """Создать UserDAO с мок коллекцией.

    Args:
        user_collections: Мок коллекция пользователей.

    Returns:
        UserDAO: DAO объект для работы с пользователями.
    """
    return UserDAO(user_collections)


@pytest.fixture
def activation_code_collection(mongo_mock):
    """Получить мок коллекцию кодов активации.

    Args:
        mongo_mock: Мок база данных.

    Returns:
        AsyncMongoMockCollection: Коллекция activation_codes.
    """
    return mongo_mock.get_activation_codes_collection()


@pytest.fixture
def activation_code_dao(activation_code_collection: AsyncMongoMockCollection):
    """Создать ActivationCodeDAO с мок коллекцией.

    Args:
        activation_code_collection: Мок коллекция кодов.

    Returns:
        ActivationCodeDAO: DAO объект для работы с кодами.
    """
    return ActivationCodeDAO(activation_code_collection)


@pytest.fixture
async def setup_indexes_for_activation_code(activation_code_collection: AsyncMongoMockCollection):
    """Создать индексы для коллекции кодов активации.

    Args:
        activation_code_collection: Мок коллекция кодов.

    Returns:
        AsyncMongoMockCollection: Коллекция с созданными индексами.
    """
    await ActivationCodeDAO.setup_indexes(activation_code_collection)
    return activation_code_collection


@pytest.fixture
def registration_collection(mongo_mock):
    """Получить мок коллекцию регистраций.

    Args:
        mongo_mock: Мок база данных.

    Returns:
        AsyncMongoMockCollection: Коллекция registrations.
    """
    return mongo_mock.get_registrations_collection()


@pytest.fixture
def registration_dao(registration_collection: AsyncMongoMockCollection):
    """Создать RegistrationDAO с мок коллекцией.

    Args:
        registration_collection: Мок коллекция регистраций.

    Returns:
        RegistrationDAO: DAO объект для работы с регистрациями.
    """
    return RegistrationDAO(registration_collection)


@pytest.fixture
async def setup_indexes_for_registration(registration_collection: AsyncMongoMockCollection):
    """Создать индексы для коллекции регистраций.

    Args:
        registration_collection: Мок коллекция регистраций.

    Returns:
        AsyncMongoMockCollection: Коллекция с созданными индексами.
    """
    await RegistrationDAO.setup_indexes(registration_collection)
    return registration_collection


@pytest.fixture
def event_collection(mongo_mock):
    """Получить мок коллекцию событий.

    Args:
        mongo_mock: Мок база данных.

    Returns:
        AsyncMongoMockCollection: Коллекция events.
    """
    return mongo_mock.get_events_collection()


@pytest.fixture
def event_dao(event_collection: AsyncMongoMockCollection):
    """Создать EventDAO с мок коллекцией.

    Args:
        event_collection: Мок коллекция событий.

    Returns:
        EventDAO: DAO объект для работы с событиями.
    """
    return EventDAO(event_collection)