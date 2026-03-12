"""Dependency контейнер для пользователей.

Модуль содержит функции для внедрения зависимостей (DI)
через FastAPI Depends.
"""

from fastapi import Depends
from app.database import db_client
from app.models.user import UserDAO
from app.models.activation_code import ActivationCodeDAO
from app.models.events import EventDAO
from app.services.auth import AuthService
from app.services.user import UserService
from app.dependency_container.event_deps import get_activation_code_dao, get_event_dao


def get_user_collections():
    """Получить коллекцию users из MongoDB.

    Returns:
        Коллекция MongoDB для пользователей.
    """
    return db_client.get_db()['users']  # type: ignore


def get_user_dao(collection=Depends(get_user_collections)) -> UserDAO:
    """Создать UserDAO с зависимостью от коллекции.

    Args:
        collection: Коллекция MongoDB (из get_user_collections).

    Returns:
        UserDAO: Data Access Object для пользователей.
    """
    return UserDAO(collection)


def get_auth_service() -> AuthService:
    """Создать AuthService.

    Returns:
        AuthService: Сервис для работы с JWT и паролями.
    """
    return AuthService()


def get_user_service(
    dao: UserDAO = Depends(get_user_dao),
    auth: AuthService = Depends(get_auth_service),
    event: EventDAO = Depends(get_event_dao),
    code: ActivationCodeDAO = Depends(get_activation_code_dao)
) -> UserService:
    """Создать UserService с зависимостями.

    Args:
        dao: UserDAO (из get_user_dao).
        auth: AuthService (из get_auth_service).

    Returns:
        UserService: Сервис для бизнес-логики пользователей.
    """
    return UserService(user_dao=dao, auth_service=auth, code_dao=code, event_dao=event)
