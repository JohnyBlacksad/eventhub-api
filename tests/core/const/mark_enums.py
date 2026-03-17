from enum import StrEnum
import pytest

def tag(value: str):
    return getattr(pytest.mark, value)

class MarkTests(StrEnum):
    UNITS = 'UNITS'

class ModuleMarks(StrEnum):
    DAO = "DAO"

class ServicesMark(StrEnum):
    EVENTS = 'EVENTS'
    USERS = 'USERS'


class FeaturesUserMark(StrEnum):
    CREATE_USER = 'CREATE_USER'
    GET_USER = 'GET_USER'
    UPDATE_USER = 'UPDATE_USER'
    DELETE_USER = 'DELETE_USER'
    UPDATE_ROLE = 'UPDATE_ROLE'
    BAN_USER = 'BAN_USER'
    GET_USERS = 'GET_USERS'

class DataBaseFunctionMark(StrEnum):
    SETUP_INDEXES = 'SETUP_INDEXES'

