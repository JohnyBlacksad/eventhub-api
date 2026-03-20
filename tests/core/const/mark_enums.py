from enum import Enum

import pytest

from tests.core.const.base_enum_marker import BaseMarkerEnum


def tag(value):
    if isinstance(value, Enum):
        marker_name = value.name
    else:
        marker_name = str(value)
    return getattr(pytest.mark, marker_name)


class MarkTests(BaseMarkerEnum):
    UNITS = ("Unit Tests", "unit")
    INTEGRATION = ("Integration Tests", "integration")
    LOAD = ("Load Tests", "load")

    def __init__(self, epic, layer):
        self.epic = epic
        self.layer = layer
        self.parent_suite = epic  #


class ModuleMarks(BaseMarkerEnum):
    DAO = "Data Access Layer"
    SERVICES = "Services Business Logic Layer"
    API = "API Endpoints Layer"

    def __init__(self, feature):
        self.feature = feature
        self.suite = feature  #


class ServicesMark(BaseMarkerEnum):
    EVENTS = "Events Service"
    USERS = "Users Service"
    AUTH = "Auth Service"
    ACTIVATION_CODE = "Activation Code Service"
    EVENT_REGISTRATION = "Event Registration Service"

    def __init__(self, sub_suite):
        self.sub_suite = sub_suite  #


class FeaturesUserMark(BaseMarkerEnum):
    CREATE_USER = ("Create User", "blocker")
    GET_USER = ("Get User", "normal")
    UPDATE_USER = ("Update User", "normal")
    DELETE_USER = ("Delete User", "blocker")
    UPDATE_ROLE = ("Update User Role", "normal")
    BAN_USER = ("Ban user", "critical")
    GET_USERS = ("Get User List", "normal")

    def __init__(self, story, severity):
        self.story = story
        self.severity = severity


class DataBaseFunctionMark(BaseMarkerEnum):
    SETUP_INDEXES = ("Database Indexes", "critical")

    def __init__(self, story, severity):
        self.story = story
        self.severity = severity


class FeaturesEventMark(BaseMarkerEnum):
    CREATE_EVENT = ("Create Event", "critical")
    GET_EVENT = ("Get Event", "normal")
    UPDATE_EVENT = ("Update Event", "normal")
    DELETE_EVENT = ("Delete Event", "critical")
    HAS_ACTIVE_EVENT = ("Has Active Event", "minor")
    DELETE_USER_EVENTS = ("Delete User Events", "critical")
    GET_EVENTS = ("Get Events List", "normal")

    def __init__(self, story, severity):
        self.story = story
        self.severity = severity


class FeaturesRegistrationMark(BaseMarkerEnum):
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


class FeaturesActivationCodeMark(BaseMarkerEnum):
    CREATE_CODE = ("Create Code", "critical")
    GET_CODE = ("Get Code", "normal")
    GET_CODES = ("Get Codes List", "normal")
    USE_CODE = ("Use Code", "critical")
    DELETE_CODE = ("Delete Code", "critical")
    FILTER_CODES = ("Filter Codes", "normal")

    def __init__(self, story, severity):
        self.story = story
        self.severity = severity


class FeaturesAuthMark(BaseMarkerEnum):
    HASH_PASSWORD = ("Hash Password", "critical")
    VERIFY_PASSWORD = ("Verify Password", "critical")
    CREATE_TOKEN = ("Create Token", "critical")
    DECODE_TOKEN = ("Decode Token", "critical")
    REFRESH_TOKEN = ("Refresh Token", "normal")

    def __init__(self, story, severity):
        self.story = story
        self.severity = severity


class UnitTag(BaseMarkerEnum):
    SMOKE = 'smoke'
    REGRESSION = 'regression'
    SLOW = 'slow'
    FAST = 'fast'
    FLAKY = 'flaky'
    CONCURENCY = 'concurency'

    def __init__(self, tag):
        self.tag = tag