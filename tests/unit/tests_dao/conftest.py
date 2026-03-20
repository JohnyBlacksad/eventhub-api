"""Фикстуры для DAO тестов EventHub API.

Модуль содержит фикстуры для тестирования DAO слоя:
- Фикстуры для UserDAO (пользователи, фабрики)
- Фикстуры для EventDAO (события, фабрики)
- Фикстуры для RegistrationDAO (регистрации, фабрики)
- Фикстуры для ActivationCodeDAO (коды активации, фабрики)
"""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from bson import ObjectId

from app.models.activation_code import ActivationCodeDAO
from app.models.events import EventDAO
from app.models.registration import RegistrationDAO
from app.models.user import UserDAO
from app.schemas.enums.event_enums.event_enums import EventStatusEnum
from app.schemas.enums.user_enums.users_status import UserRoleEnum
from tests.core.event_data_factory.fake_event_data import event_faker
from tests.core.user_data_factory.fake_user_data import faker
from tests.mock.mongo_mock import get_mongo_mock



@pytest.fixture
async def created_user(mock_user_dao: UserDAO):
    """Создать тестового пользователя и вернуть его из БД.

    Args:
        mock_user_dao: UserDAO с мок коллекцией.

    Returns:
        dict: Документ пользователя из БД.
    """
    user = faker.get_user_register_data_dict()
    create_user_id = await mock_user_dao.create_user(user)
    db_user = await mock_user_dao.get_user_by_id(create_user_id)
    return db_user


@pytest.fixture
async def base_users(mock_user_dao: UserDAO):
    """Создать 10 тестовых пользователей и вернуть UserDAO.

    Args:
        mock_user_dao: UserDAO с мок коллекцией.

    Returns:
        UserDAO: DAO объект с созданной группой пользователей.
    """
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
        user_data["created_at"] = now - timedelta(seconds=10)
        user_id = await mock_user_dao.create_user(user_data)
        db_user = await mock_user_dao.get_user_by_id(user_id)
        early_users.append(db_user)

    # Средние пользователи (сейчас)
    middle_users = []
    for _ in range(5):
        user_data = faker.get_user_register_data_dict()
        user_data["created_at"] = now
        user_id = await mock_user_dao.create_user(user_data)
        db_user = await mock_user_dao.get_user_by_id(user_id)
        middle_users.append(db_user)

    # Поздние пользователи (через 10 секунд)
    late_users = []
    for _ in range(2):
        user_data = faker.get_user_register_data_dict()
        user_data["created_at"] = now + timedelta(seconds=10)
        user_id = await mock_user_dao.create_user(user_data)
        db_user = await mock_user_dao.get_user_by_id(user_id)
        late_users.append(db_user)

    return {"early": early_users, "middle": middle_users, "late": late_users, "now": now}


@pytest.fixture
async def created_event(event_dao: EventDAO):
    """Создать тестовое событие и вернуть его из БД.

    Args:
        event_dao: EventDAO с мок коллекцией.

    Returns:
        dict: Документ события из БД.
    """
    event_data = event_faker.get_event_data_dict()
    event_id = await event_dao.create_event(event_data)
    event = await event_dao.get_event(event_id)
    return event


@pytest.fixture
async def event_factory_for_user(event_dao: EventDAO, created_user):
    """Фабрика для создания событий у существующего пользователя.

    Args:
        event_dao: EventDAO с мок коллекцией.
        created_user: Существующий тестовый пользователь.

    Returns:
        callable: Асинхронная функция factory(status, count, start_date_days_offset).
    """

    async def aplicate_status_event(status: EventStatusEnum, count: int = 1, start_date_days_offset: int = 0):
        user_id = created_user["_id"]
        event_list = []
        events_ids = []

        for _ in range(count):
            event_data = event_faker.get_event_data_dict(
                status=status,
                created_by=user_id,
                startDate=datetime.now(timezone.utc) + timedelta(days=start_date_days_offset),
            )
            event_id = await event_dao.create_event(event_data)
            event = await event_dao.get_event(event_id)
            event_list.append(event)
            events_ids.append(event_id)

        if len(event_list) > 1:
            return user_id, event_list, events_ids

        return user_id, event_list[0], events_ids[0]

    return aplicate_status_event


@pytest.fixture
async def created_registration(registration_dao: RegistrationDAO, created_user: dict, created_event: dict):
    """Создать регистрацию для пользователя на событие.

    Args:
        registration_dao: RegistrationDAO с мок коллекцией.
        created_user: Существующий тестовый пользователь.
        created_event: Существующее тестовое событие.

    Returns:
        dict: Документ регистрации из БД.
    """
    user_id = created_user["_id"]
    event_id = created_event["_id"]

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


@pytest.fixture
def code_factory_data():
    """Фабрика данных для создания кода активации.

    Returns:
        dict: Данные для создания кода.
    """

    def factory(role=None, code=None) -> dict:
        from app.schemas.enums.user_enums.users_status import UserRoleEnum

        return {"role": role or UserRoleEnum.ORGANIZER, "code": code or "test-code-default"}

    return factory


@pytest.fixture
async def created_activation_code(activation_code_dao: ActivationCodeDAO, code_factory_data):
    """Создать код активации по умолчанию.

    Args:
        activation_code_dao: ActivationCodeDAO с мок коллекцией.
        code_factory_data: Фабрика данных для кода.

    Returns:
        dict: Документ кода активации из БД.
    """
    code_data = code_factory_data()
    code_id = await activation_code_dao.create_code(code_data)
    code = await activation_code_dao.get_code(code_id)
    return code


@pytest.fixture
async def activation_code_factory(activation_code_dao: ActivationCodeDAO):
    """Фабрика для создания кодов активации.

    Args:
        role: Роль кода (по умолчанию ORGANIZER).
        code: Строка кода (по умолчанию генерируется).
        is_used: Флаг использования (по умолчанию False).
        created_at: Время создания (по умолчанию сейчас).

    Returns:
        dict: Созданный код активации.
    """

    async def factory(
        role: UserRoleEnum | None = None,
        code: str | None = None,
        is_used: bool = False,
        created_at: datetime | None = None,
    ) -> dict:
        code_data = {
            "role": role or UserRoleEnum.ORGANIZER,
            "code": code or str(uuid4()),
            "created_at": created_at or datetime.now(timezone.utc),
        }

        code_id = await activation_code_dao.create_code(code_data)

        # Если нужен использованный код - обновляем вручную
        if is_used:
            await activation_code_dao.collection.update_one({"_id": ObjectId(code_id)}, {"$set": {"is_used": True}})

        created_code = await activation_code_dao.get_code(code_id)

        assert created_code

        return created_code

    return factory


@pytest.fixture
async def activation_codes_factory(activation_code_dao: ActivationCodeDAO):
    """Фабрика для создания множественных кодов активации.

    Args:
        count: Количество кодов (по умолчанию 1).
        role: Роль кода (применяется ко всем).
        is_used_list: Список флагов is_used для каждого кода.
        created_at_list: Список времён создания для каждого кода.

    Returns:
        list[dict]: Список созданных кодов.
    """

    async def factory(
        count: int = 1,
        role: UserRoleEnum | None = None,
        is_used_list: list[bool] | None = None,
        created_at_list: list[datetime] | None = None,
    ) -> list[dict]:
        codes = []

        for i in range(count):
            code_data = {
                "role": role or UserRoleEnum.ORGANIZER,
                "code": str(uuid4()),
            }

            code_id = await activation_code_dao.create_code(code_data)

            # Обновляем created_at и is_used после создания
            update_data = {}
            if created_at_list and i < len(created_at_list):
                update_data["created_at"] = created_at_list[i]

            if is_used_list and i < len(is_used_list) and is_used_list[i]:
                update_data["is_used"] = True

            if update_data:
                await activation_code_dao.collection.update_one({"_id": ObjectId(code_id)}, {"$set": update_data})

            created_code = await activation_code_dao.get_code(code_id)
            codes.append(created_code)

        return codes

    return factory
