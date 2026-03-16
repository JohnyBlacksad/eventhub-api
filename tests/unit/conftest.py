from datetime import datetime, timedelta, timezone

import pytest
from tests.mock.mongo_mock import get_mongo_mock
from app.models.user import UserDAO
from mongomock_motor import AsyncMongoMockCollection
from tests.core.user_data_factory.fake_user_data import faker


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