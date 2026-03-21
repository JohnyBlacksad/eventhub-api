"""Фикстуры для тестирования сервисов EventHub API.

Модуль содержит фикстуры для тестирования слоя сервисов:
- Auth сервис (JWT, bcrypt)
- User сервис (бизнес-логика пользователей)
- Event сервис (бизнес-логика событий)
- ActivationCode сервис (коды активации)
"""

import pytest

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