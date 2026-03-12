"""Dependency контейнер для событий.

Модуль содержит функции для внедрения зависимостей (DI)
через FastAPI Depends для событий, регистраций и кодов активации.
"""

from fastapi import Depends
from app.database import db_client
from app.models.events import EventDAO
from app.models.registration import RegistrationDAO
from app.models.activation_code import ActivationCodeDAO
from app.services.event import EventService


def get_events_collection():
    """Получить коллекцию events из MongoDB.

    Returns:
        Коллекция MongoDB для событий.
    """
    return db_client.get_db()['events']  # type: ignore


def get_event_dao(collection=Depends(get_events_collection)) -> EventDAO:
    """Создать EventDAO с зависимостью от коллекции.

    Args:
        collection: Коллекция MongoDB (из get_events_collection).

    Returns:
        EventDAO: Data Access Object для событий.
    """
    return EventDAO(collection)


def get_registrations_collection():
    """Получить коллекцию registrations из MongoDB.

    Returns:
        Коллекция MongoDB для регистраций.
    """
    return db_client.get_db()['registrations']  # type: ignore


def get_registration_dao(collection=Depends(get_registrations_collection)) -> RegistrationDAO:
    """Создать RegistrationDAO с зависимостью от коллекции.

    Args:
        collection: Коллекция MongoDB (из get_registrations_collection).

    Returns:
        RegistrationDAO: Data Access Object для регистраций.
    """
    return RegistrationDAO(collection)


def get_activation_code_collection():
    """Получить коллекцию org_code из MongoDB.

    Returns:
        Коллекция MongoDB для кодов активации.
    """
    return db_client.get_db()['org_code']  # type: ignore


def get_activation_code_dao(collection=Depends(get_activation_code_collection)) -> ActivationCodeDAO:
    """Создать ActivationCodeDAO с зависимостью от коллекции.

    Args:
        collection: Коллекция MongoDB (из get_activation_code_collection).

    Returns:
        ActivationCodeDAO: Data Access Object для кодов активации.
    """
    return ActivationCodeDAO(collection)


def get_event_service(
    event_dao: EventDAO = Depends(get_event_dao),
    registration_dao: RegistrationDAO = Depends(get_registration_dao)
) -> EventService:
    """Создать EventService с зависимостями.

    Args:
        event_dao: EventDAO (из get_event_dao).
        registration_dao: RegistrationDAO (из get_registration_dao).

    Returns:
        EventService: Сервис для бизнес-логики событий.
    """
    return EventService(
        event_dao=event_dao,
        registration_dao=registration_dao
    )
