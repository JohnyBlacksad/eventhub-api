from datetime import datetime, timedelta, timezone


import pytest
from app.models.events import EventDAO
from app.models.registration import RegistrationDAO
from app.schemas.enums.event_enums.event_enums import EventStatusEnum
from tests.mock.mongo_mock import get_mongo_mock
from app.models.user import UserDAO
from mongomock_motor import AsyncMongoMockCollection
from tests.core.user_data_factory.fake_user_data import faker
from tests.core.event_data_factory.fake_event_data import event_faker

@pytest.fixture
def mongo_mock():
    db = get_mongo_mock()
    return db

@pytest.fixture
def user_collections(mongo_mock):
    user_collection = mongo_mock.get_users_collection()
    return user_collection

@pytest.fixture
def mock_user_dao(user_collections: AsyncMongoMockCollection):
    return UserDAO(user_collections)

@pytest.fixture
async def created_user(mock_user_dao: UserDAO):
    user = faker.get_user_register_data_dict()
    create_user_id = await mock_user_dao.create_user(user)
    db_user = await mock_user_dao.get_user_by_id(create_user_id)
    return db_user

@pytest.fixture
async def base_users(mock_user_dao: UserDAO):
    users_list = [faker.get_user_register_data_dict() for _ in range(10)]
    for user in users_list:
        await mock_user_dao.create_user(user)

    return mock_user_dao

@pytest.fixture
async def users_with_different_dates(mock_user_dao: UserDAO) -> dict[str, list | datetime]:
    """Создаёт пользователей с разными created_at.

    Возвращает dict с группами пользователей:
    {
        'early': [...],      # created_at = now - 10 sec
        'middle': [...],     # created_at = now
        'late': [...]        # created_at = now + 10 sec
    }
    """
    now = datetime.now(timezone.utc)

    # Ранние пользователи (10 секунд назад)
    early_users = []
    for _ in range(3):
        user_data = faker.get_user_register_data_dict()
        user_data['created_at'] = now - timedelta(seconds=10)
        user_id = await mock_user_dao.create_user(user_data)
        db_user = await mock_user_dao.get_user_by_id(user_id)
        early_users.append(db_user)

    # Средние пользователи (сейчас)
    middle_users = []
    for _ in range(5):
        user_data = faker.get_user_register_data_dict()
        user_data['created_at'] = now
        user_id = await mock_user_dao.create_user(user_data)
        db_user = await mock_user_dao.get_user_by_id(user_id)
        middle_users.append(db_user)

    # Поздние пользователи (через 10 секунд)
    late_users = []
    for _ in range(2):
        user_data = faker.get_user_register_data_dict()
        user_data['created_at'] = now + timedelta(seconds=10)
        user_id = await mock_user_dao.create_user(user_data)
        db_user = await mock_user_dao.get_user_by_id(user_id)
        late_users.append(db_user)

    return {
        'early': early_users,
        'middle': middle_users,
        'late': late_users,
        'now': now
    }

@pytest.fixture
def event_collection(mongo_mock):
    return mongo_mock.get_events_collection()

@pytest.fixture
def event_dao(event_collection: AsyncMongoMockCollection):
    return EventDAO(event_collection)

@pytest.fixture
async def created_event(event_dao: EventDAO):
    event_data = event_faker.get_event_data_dict()
    event_id = await event_dao.create_event(event_data)
    event = await event_dao.get_event(event_id)
    return event

@pytest.fixture
async def event_factory_for_user(event_dao: EventDAO, created_user):
    """Фабрика для создания событий у существующего пользователя."""

    async def aplicate_status_event(
            status: EventStatusEnum,
            count: int = 1,
            start_date_days_offset: int = 0
        ):

        user_id = created_user['_id']
        event_list = []
        events_ids = []

        for _ in range(count):
            event_data = event_faker.get_event_data_dict(
                status=status,
                created_by=user_id,
                startDate=datetime.now(timezone.utc) + timedelta(days=start_date_days_offset))
            event_id = await event_dao.create_event(event_data)
            event = await event_dao.get_event(event_id)
            event_list.append(event)
            events_ids.append(event_id)

        if len(event_list) > 1:
            return user_id, event_list, events_ids

        return user_id, event_list[0], events_ids[0]

    return aplicate_status_event


@pytest.fixture
def registration_collection(mongo_mock):
    """Получить коллекцию registrations из mock БД."""
    return mongo_mock.get_registrations_collection()


@pytest.fixture
def registration_dao(registration_collection: AsyncMongoMockCollection):
    """Создать RegistrationDAO с mock коллекцией."""
    return RegistrationDAO(registration_collection)


@pytest.fixture
async def setup_indexes_for_registration(registration_collection: AsyncMongoMockCollection):
    """Инициализировать индексы для коллекции регистраций."""
    await RegistrationDAO.setup_indexes(registration_collection)
    return registration_collection


@pytest.fixture
async def created_registration(registration_dao: RegistrationDAO, created_user: dict, created_event: dict):
    """Создать регистрацию для пользователя на событие."""
    user_id = created_user['_id']
    event_id = created_event['_id']

    await registration_dao.add_registration(str(event_id), str(user_id))

    registration = await registration_dao.get_existing_registration(str(event_id), str(user_id))
    return registration


@pytest.fixture
async def user_factory(mock_user_dao: UserDAO):
    """Фабрика для создания пользователей.

    Возвращает ID созданного пользователя.
    """
    async def factory() -> str:
        user_data = faker.get_user_register_data_dict()
        user_id = await mock_user_dao.create_user(user_data)
        return str(user_id)

    return factory


@pytest.fixture
async def registration_factory(registration_dao: RegistrationDAO, user_factory):
    """Фабрика для создания регистраций.

    Args:
        event_id: ID события для регистрации.
        user_id: ID пользователя (если None, создаётся новый через user_factory).

    Returns:
        dict: Созданная регистрация.
    """
    async def factory(event_id: str, user_id: str | None = None) -> dict:
        if user_id is None:
            user_id = await user_factory()

        assert user_id

        await registration_dao.add_registration(event_id, user_id)
        registration = await registration_dao.get_existing_registration(event_id, user_id)

        assert registration

        return registration

    return factory


@pytest.fixture
async def event_registrations_factory(registration_dao: RegistrationDAO, user_factory):
    """Фабрика для создания множественных регистраций на одно событие.

    Args:
        event_id: ID события.
        count: Количество регистраций (по умолчанию 1).

    Returns:
        list[dict]: Список регистраций.
    """
    async def factory(event_id: str, count: int = 1) -> list[dict]:
        registrations = []
        for _ in range(count):
            user_id = await user_factory()
            await registration_dao.add_registration(event_id, user_id)
            registration = await registration_dao.get_existing_registration(event_id, user_id)
            registrations.append(registration)
        return registrations

    return factory