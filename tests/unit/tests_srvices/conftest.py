"""Фикстуры для тестирования сервисов EventHub API.

Модуль содержит фикстуры для тестирования слоя сервисов:
- Auth сервис (JWT, bcrypt)
- User сервис (бизнес-логика пользователей)
- Event сервис (бизнес-логика событий)
- ActivationCode сервис (коды активации)
"""

from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import uuid4

import pytest
from bson import ObjectId

from app.config_models.auth_config import AuthConfig
from app.models.activation_code import ActivationCodeDAO
from app.models.events import EventDAO
from app.models.registration import RegistrationDAO
from app.models.user import UserDAO
from app.schemas.enums.user_enums.users_status import UserRoleEnum
from app.schemas.enums.event_enums.event_enums import EventStatusEnum
from app.schemas.event import EventCreateModel
from app.services.activation_code import ActivationCodeService
from app.services.auth import AuthService
from app.services.event import EventService
from app.services.user import UserService
from tests.core.auth_data_factory.fake_auth_data import auth_faker
from tests.core.user_data_factory.fake_user_data import faker
from tests.core.event_data_factory.fake_event_data import event_faker


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


@pytest.fixture
def user_service(
    mock_user_dao: UserDAO,
    auth_service: AuthService,
    activation_code_dao: ActivationCodeDAO,
    event_dao: EventDAO
    ):

    """
    Создать User Service с тестовой конфигурацией.

    Args:
        mock_user_dao: Мок `UserDAO` на mongomock-motor
        auth_service: Мок сервиса аутентификации `AuthService`
        activation_code_dao: Мок `ActivationCodeDAO` на mongomock-morot
        event_dao: Мок `EventDAO` на mongomock-motor

    Returns:
        UserService: Сервис с бизнес логикой пользователей
    """

    return UserService(
        user_dao=mock_user_dao,
        auth_service=auth_service,
        code_dao=activation_code_dao,
        event_dao=event_dao
    )


@pytest.fixture
def event_service(
    event_dao: EventDAO,
    registration_dao: RegistrationDAO
) -> EventService:
    """Создать EventService с мок зависимостями.

    Args:
        event_dao: EventDAO с мок коллекцией.
        registration_dao: RegistrationDAO с мок коллекцией.

    Returns:
        EventService: Сервис событий для тестов.
    """
    return EventService(
        event_dao,
        registration_dao
    )

@pytest.fixture
def code_service(activation_code_dao: ActivationCodeDAO):
    """Создать ActivationCodeService с мок зависимостями.

    Args:
        activation_code_dao: ActivationCodeDAO с мок коллекцией.

    Returns:
        ActivationCodeService: Сервис кодов активации для тестов.
    """
    return ActivationCodeService(activation_code_dao)

@pytest.fixture
async def created_user(user_service: UserService):
    """Создать тестового пользователя через UserService.

    Args:
        user_service: UserService для регистрации.

    Returns:
        tuple[UserResponseModel, str]: Кортеж (пользователь, пароль).
    """
    user = faker.get_user_register_model()
    password = user.password.get_secret_value()
    create_user = await user_service.register_user(user)

    return create_user, password

@pytest.fixture
async def banned_user(user_service: UserService, created_user):
    """Создать забаненного тестового пользователя.

    Args:
        user_service: UserService для операций.
        created_user: Фикстура с созданным пользователем.

    Returns:
        tuple[UserResponseModel, str]: Кортеж (забаненный пользователь, пароль).
    """
    user, password = created_user
    user = await user_service.set_ban_user(user.id, is_banned=True)

    return user, password

@pytest.fixture
async def created_user_with_event(
    user_service: UserService,
    event_service: EventService,
    created_user
):
    """Создать пользователя-организатора с активным событием.

    Args:
        user_service: UserService для операций.
        event_service: EventService для создания события.
        created_user: Фикстура с созданным пользователем.

    Returns:
        tuple[UserResponseModel, dict]: Кортеж (организатор, событие).
    """
    user, *_ = created_user

    organizer = await user_service.change_user_role(
        user_id=user.id,
        new_role=UserRoleEnum.ORGANIZER
    )
    event_data = event_faker.get_event_data_dict(status=EventStatusEnum.PUBLISHED)

    event = await event_service.create_event(
        EventCreateModel.model_validate(event_data, from_attributes=True),
        organizer.id
    )

    return organizer, event


@pytest.fixture
async def created_user_with_limited_event(
    user_service: UserService,
    event_service: EventService,
    created_user
):
    """Создать пользователя-организатора с событием с лимитом участников.

    Args:
        user_service: UserService для операций.
        event_service: EventService для создания события.
        created_user: Фикстура с созданным пользователем.

    Returns:
        tuple[UserResponseModel, dict]: Кортеж (организатор, событие с max_participants=5).
    """
    user, *_ = created_user

    organizer = await user_service.change_user_role(
        user_id=user.id,
        new_role=UserRoleEnum.ORGANIZER
    )
    event_data = event_faker.get_event_data_dict(
        status=EventStatusEnum.PUBLISHED,
        max_participants=5
    )

    event = await event_service.create_event(
        EventCreateModel.model_validate(event_data, from_attributes=True),
        organizer.id
    )

    return organizer, event

@pytest.fixture
async def organizer_code(code_service: ActivationCodeService):
    """Создать код активации для роли ORGANIZER.

    Args:
        code_service: ActivationCodeService для создания кода.

    Returns:
        ActivationCodeModelResponse: Данные созданного кода.
    """
    code = await code_service.create_code()
    return code

@pytest.fixture
async def admin_code(code_service: ActivationCodeService):
    """Создать код активации для роли ADMIN.

    Args:
        code_service: ActivationCodeService для создания кода.

    Returns:
        ActivationCodeModelResponse: Данные созданного кода.
    """
    code = await code_service.create_code(role=UserRoleEnum.ADMIN)
    return code


@pytest.fixture
async def multiple_users(user_service: UserService):
    """Создать 10 тестовых пользователей.

    Returns:
        list[UserResponseModel]: Список созданных пользователей.
    """
    users = []
    for _ in range(10):
        user_data = faker.get_user_register_model()
        user = await user_service.register_user(user_data)
        users.append(user)
    return users


@pytest.fixture
async def organizer_user(user_service: UserService):
    """Создать пользователя с ролью ORGANIZER."""
    user_data = faker.get_user_register_model()
    user = await user_service.register_user(user_data)
    organizer = await user_service.change_user_role(user.id, UserRoleEnum.ORGANIZER)
    return organizer


@pytest.fixture
async def admin_user(user_service: UserService):
    """Создать пользователя с ролью ADMIN."""
    user_data = faker.get_user_register_model()
    user = await user_service.register_user(user_data)
    admin = await user_service.change_user_role(user.id, UserRoleEnum.ADMIN)
    return admin

@pytest.fixture
async def event_factory_for_user(event_service: EventService, multiple_users):

    events = []
    for user in multiple_users:
        event_data = event_faker.get_create_event_model()

        event = await event_service.create_event(event_data, user.id)
        events.append(event)

    return events

@pytest.fixture
async def event_factory(event_service: EventService):

    async def factory(
            count: int = 1,
            status_event: Optional[EventStatusEnum] = None,
            start_date_event: Optional[datetime] = None,
            end_date_event: Optional[datetime] = None,
            ):
        events = []
        for _ in range(count):
            event_data = event_faker.get_event_data_dict(
                status=status_event if status_event else EventStatusEnum.PUBLISHED,
                start_date=start_date_event if start_date_event else datetime.now(timezone.utc) + timedelta(days=15),
                end_date=end_date_event if end_date_event else datetime.now(timezone.utc) + timedelta(days=30)
            )
            del event_data['created_by']
            del event_data['created_at']
            event_model = EventCreateModel.model_validate(event_data, from_attributes=True)
            user_id = event_faker.generate_random_id()
            event = await event_service.create_event(event_model, user_id)

            events.append(event)

        return events

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

    async def factory(event_id: str, user_id: str | None = None, count: int = 1) -> list[dict]:
        registrations = []
        for _ in range(count):
            # Создаём нового пользователя для каждой регистрации если user_id не указан
            current_user_id = user_id if user_id else await user_factory()

            await registration_dao.add_registration(event_id, current_user_id) # type: ignore
            registration = await registration_dao.get_existing_registration(event_id, current_user_id) # type: ignore

            assert registration

            registrations.append(registration)

        return registrations

    return factory

@pytest.fixture
async def user_factory(user_service: UserService):
    """Фабрика для создания пользователей.

    Returns:
        str: ID созданного пользователя.
    """

    async def factory() -> str:
        from tests.core.user_data_factory.fake_user_data import faker
        user_data = faker.get_user_register_model()
        user = await user_service.register_user(user_data)
        return str(user.id)

    return factory


@pytest.fixture
def code_factory_data():
    """Фабрика данных для создания кода активации.

    Returns:
        dict: Данные для создания кода.
    """

    def factory(role=None, code=None) -> dict:
        return {"role": role or UserRoleEnum.ORGANIZER, "code": code or str(uuid4())}

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