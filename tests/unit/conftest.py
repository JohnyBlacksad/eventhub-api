import pytest

from mongomock_motor import AsyncMongoMockCollection
from app.models.activation_code import ActivationCodeDAO
from app.models.events import EventDAO
from app.models.registration import RegistrationDAO
from app.models.user import UserDAO
from tests.mock.mongo_mock import get_mongo_mock

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