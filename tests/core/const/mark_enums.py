from tests.core.const.base_enum_marker import BaseMarkerEnum
from enum import Enum
import pytest

def tag(value):
    if isinstance(value, Enum):
        marker_name = value.name
    else:
        marker_name = str(value)
    return getattr(pytest.mark, marker_name)

class MarkTests(BaseMarkerEnum):
    UNITS = ('Unit Tests', 'unit')
    INTEGRATION = ('Integration Tests', 'integration')
    LOAD = ('Load Tests', 'load')

    def __init__(self, epic, layer):
        self.epic = epic
        self.layer = layer
        self.parent_suite = epic #

class ModuleMarks(BaseMarkerEnum):
    DAO = 'Data Access Layer'
    SERVICES = 'Services Business Logic Layer'
    API = 'API Endpoints Layer'

    def __init__(self, feature):
        self.feature = feature
        self.suite = feature #

class ServicesMark(BaseMarkerEnum):
    EVENTS = 'Events Service'
    USERS = 'Users Service'
    AUTH = 'Auth Service'
    ACTIVATION_CODE = 'Activation Code Service'
    EVENT_REGISTRATION = 'Event Registration Service'

    def __init__(self, feature):
        self.feature = feature
        self.sub_suite = feature #


class FeaturesUserMark(BaseMarkerEnum):
    CREATE_USER = ('Create User', "BLOCKER")
    GET_USER = ('Get User', 'NORMAL')
    UPDATE_USER = ('Update User', 'NORMAL')
    DELETE_USER = ('Delete User', 'BLOCKER')
    UPDATE_ROLE = ('Update User Role', 'NORMAL')
    BAN_USER = ('Ban user', "CRITICAL")
    GET_USERS = ('Get User List', "NORMAL")

    def __init__(self, story, severity):
        self.story = story
        self.severity = severity

class DataBaseFunctionMark(BaseMarkerEnum):
    SETUP_INDEXES = ('Database Indexes', "CRITICAL")

    def __init__(self, story, severity):
        self.story = story
        self.severity = severity

class FeaturesEventMark(BaseMarkerEnum):
    CREATE_EVENT = ('Create Event', 'CRITICAL')
    GET_EVENT = ('Get Event', 'NORMAL')
    UPDATE_EVENT = ('Update Event', "NORMAL")
    DELETE_EVENT = ('Delete Event', "CRITICAL")
    HAS_ACTIVE_EVENT = ('Has Active Event', 'MINOR')
    DELETE_USER_EVENTS = ('Delete User Events', 'CRITICAL')
    GET_EVENTS = ('Get Events List', 'NORMAL')

    def __init__(self, story, severity):
        self.story = story
        self.severity = severity

