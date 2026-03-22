"""Enum'ы с маркерами pytest для Allure отчётности.

Модуль содержит систему маркеров для категоризации тестов:
- MarkTests — тип теста (unit, integration, load) → epic, layer
- ModuleMarks — слой архитектуры (DAO, services, API) → feature, suite
- ServicesMark — конкретный сервис → sub_suite
- FeaturesUserMark — операции с пользователями → story, severity
- FeaturesEventMark — операции с событиями → story, severity
- FeaturesRegistrationMark — операции с регистрациями → story, severity
- FeaturesActivationCodeMark — операции с кодами активации → story, severity
- FeaturesAuthMark — операции аутентификации → story, severity
- DataBaseFunctionMark — функции БД (setup indexes) → story, severity
- UnitTag — дополнительные теги (smoke, regression, fast, slow, flaky, concurrency)

Использование:
    @tag(MarkTests.UNITS)
    @tag(ModuleMarks.DAO)
    @tag(ServicesMark.USERS)
    @tag(FeaturesUserMark.CREATE_USER)
    class TestUserDAO:
        @tag(FeaturesUserMark.CREATE_USER)
        async def test_create_user(self, ...):
"""

from enum import Enum

import pytest

from tests.core.const.base_enum_marker import BaseMarkerEnum


def tag(value):
    """Создать pytest маркер из enum или значения.

    Args:
        value: Enum member или строка для создания маркера.

    Returns:
        pytest.mark: Маркер для использования с тестами.
    """
    if isinstance(value, Enum):
        marker_name = value.name
    else:
        marker_name = str(value)
    return getattr(pytest.mark, marker_name)


class MarkTests(BaseMarkerEnum):
    """Маркеры типа теста (epic, layer).

    Attributes:
        UNITS: Unit тесты
        INTEGRATION: Integration тесты
        LOAD: Load тесты
    """
    UNITS = ("Unit Tests", "unit")
    INTEGRATION = ("Integration Tests", "integration")
    LOAD = ("Load Tests", "load")

    def __init__(self, epic, layer):
        self.epic = epic
        self.layer = layer
        self.parent_suite = epic  # Для совместимости
        self.tag = layer #

class ModuleMarks(BaseMarkerEnum):
    """Маркеры слоя архитектуры (feature, suite).

    Attributes:
        DAO: Data Access Object слой
        SERVICES: Service layer бизнес-логика
        API: API endpoints слой
    """
    DAO = "Data Access Layer"
    SERVICES = "Services Business Logic Layer"
    API = "API Endpoints Layer"

    def __init__(self, feature):
        self.feature = feature
        self.suite = feature  # Для совместимости
        self.tag = feature #

class ServicesMark(BaseMarkerEnum):
    """Маркеры конкретных сервисов (sub_suite).

    Attributes:
        EVENTS: EventService
        USERS: UserService
        AUTH: AuthService
        ACTIVATION_CODE: ActivationCodeService
        EVENT_REGISTRATION: Event registration service
    """
    EVENTS = "Events Service"
    USERS = "Users Service"
    AUTH = "Auth Service"
    ACTIVATION_CODE = "Activation Code Service"
    EVENT_REGISTRATION = "Event Registration Service"

    def __init__(self, sub_suite):
        self.sub_suite = sub_suite
        self.tag  = sub_suite #

class FeaturesUserMark(BaseMarkerEnum):
    """Маркеры операций с пользователями (story, severity).

    Attributes:
        CREATE_USER: Создание пользователя
        GET_USER: Получение пользователя
        UPDATE_USER: Обновление пользователя
        DELETE_USER: Удаление пользователя
        UPDATE_ROLE: Смена роли пользователя
        BAN_USER: Бан/разбан пользователя
        GET_USERS: Получение списка пользователей
    """
    CREATE_USER = ("Create User", "blocker")
    GET_USER = ("Get User", "normal")
    UPDATE_USER = ("Update User", "normal")
    DELETE_USER = ("Delete User", "blocker")
    UPDATE_ROLE = ("Update User Role", "normal")
    BAN_USER = ("Ban user", "critical")
    GET_USERS = ("Get User List", "normal")
    AUTH_USER = ('User authorization', 'blocker')

    def __init__(self, story, severity):
        self.story = story
        self.severity = severity
        self.tag  = story


class DataBaseFunctionMark(BaseMarkerEnum):
    """Маркеры функций базы данных (story, severity).

    Attributes:
        SETUP_INDEXES: Создание индексов MongoDB
    """
    SETUP_INDEXES = ("Database Indexes", "critical")

    def __init__(self, story, severity):
        self.story = story
        self.severity = severity
        self.tag  = story


class FeaturesEventMark(BaseMarkerEnum):
    """Маркеры операций с событиями (story, severity).

    Attributes:
        CREATE_EVENT: Создание события
        GET_EVENT: Получение события
        UPDATE_EVENT: Обновление события
        DELETE_EVENT: Удаление события
        HAS_ACTIVE_EVENT: Проверка активных событий
        DELETE_USER_EVENTS: Удаление событий пользователя
        GET_EVENTS: Получение списка событий
        EVENT_REGISTRATION: Регистрация на событие
    """
    CREATE_EVENT = ("Create Event", "critical")
    GET_EVENT = ("Get Event", "normal")
    UPDATE_EVENT = ("Update Event", "normal")
    DELETE_EVENT = ("Delete Event", "critical")
    HAS_ACTIVE_EVENT = ("Has Active Event", "minor")
    DELETE_USER_EVENTS = ("Delete User Events", "critical")
    GET_EVENTS = ("Get Events List", "normal")
    EVENT_REGISTRATION = ("Event Registration", "normal")

    def __init__(self, story, severity):
        self.story = story
        self.severity = severity
        self.tag  = story


class FeaturesRegistrationMark(BaseMarkerEnum):
    """Маркеры операций с регистрациями (story, severity).

    Attributes:
        ADD_REGISTRATION: Добавление регистрации
        REMOVE_REGISTRATION: Удаление регистрации
        GET_EVENT_REGISTRATIONS: Получение регистраций события
        GET_USER_REGISTRATIONS: Получение регистраций пользователя
        GET_EXISTING_REGISTRATION: Проверка существующей регистрации
        DELETE_ALL_REGISTRATIONS_FOR_EVENT: Удаление всех регистраций события
        SET_DELETION_TIME_FOR_EVENT: Установка времени удаления
        DELETE_REGISTRATION_BY_USER: Удаление регистраций пользователя
    """
    ADD_REGISTRATION = ("Add Registration", "critical")
    REMOVE_REGISTRATION = ("Remove Registration", "critical")
    GET_EVENT_REGISTRATIONS = ("Get Event Registrations", "normal")
    GET_USER_REGISTRATIONS = ("Get User Registrations", "normal")
    GET_EXISTING_REGISTRATION = ("Get Existing Registration", "normal")
    DELETE_ALL_REGISTRATIONS_FOR_EVENT = ("Delete All Registrations For Event", "critical")
    SET_DELETION_TIME_FOR_EVENT = ("Set Deletion Time For Event", "normal")
    DELETE_REGISTRATION_BY_USER = ("Delete Registration By User", "critical")

    def __init__(self, story, severity):
        self.story = story
        self.severity = severity
        self.tag  = story


class FeaturesActivationCodeMark(BaseMarkerEnum):
    """Маркеры операций с кодами активации (story, severity).

    Attributes:
        CREATE_CODE: Создание кода активации
        GET_CODE: Получение кода по ID
        GET_CODES: Получение списка кодов
        USE_CODE: Использование кода
        DELETE_CODE: Удаление кода
        FILTER_CODES: Фильтрация кодов
    """
    CREATE_CODE = ("Create Code", "critical")
    GET_CODE = ("Get Code", "normal")
    GET_CODES = ("Get Codes List", "normal")
    USE_CODE = ("Use Code", "critical")
    DELETE_CODE = ("Delete Code", "critical")
    FILTER_CODES = ("Filter Codes", "normal")

    def __init__(self, story, severity):
        self.story = story
        self.severity = severity
        self.tag  = story


class FeaturesAuthMark(BaseMarkerEnum):
    """Маркеры операций аутентификации (story, severity).

    Attributes:
        HASH_PASSWORD: Хеширование пароля
        VERIFY_PASSWORD: Верификация пароля
        CREATE_TOKEN: Создание JWT токена
        DECODE_TOKEN: Декодирование JWT токена
        REFRESH_TOKEN: Обновление токенов
    """
    HASH_PASSWORD = ("Hash Password", "critical")
    VERIFY_PASSWORD = ("Verify Password", "critical")
    CREATE_TOKEN = ("Create Token", "critical")
    DECODE_TOKEN = ("Decode Token", "critical")
    REFRESH_TOKEN = ("Refresh Token", "normal")

    def __init__(self, story, severity):
        self.story = story
        self.severity = severity
        self.tag  = story

class UnitTag(BaseMarkerEnum):
    """Дополнительные теги для тестов.

    Attributes:
        SMOKE: Smoke тесты
        REGRESSION: Regression тесты
        SLOW: Медленные тесты
        FAST: Быстрые тесты
        FLAKY: Нестабильные тесты
        CONCURENCY: Тесты конкурентности
    """
    SMOKE = 'smoke'
    REGRESSION = 'regression'
    SLOW = 'slow'
    FAST = 'fast'
    FLAKY = 'flaky'
    CONCURENCY = 'concurency'

    def __init__(self, tag):
        self.tag = tag