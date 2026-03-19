from fastapi import Depends

from app.database import db_client
from app.models.activation_code import ActivationCodeDAO
from app.services.activation_code import ActivationCodeService


def get_activation_code_collection():
    """Получить коллекцию org_code из MongoDB.

    Returns:
        Коллекция MongoDB для кодов активации.
    """
    return db_client.get_db()["org_code"]  # type: ignore


def get_activation_code_dao(collection=Depends(get_activation_code_collection)) -> ActivationCodeDAO:
    """Создать ActivationCodeDAO с зависимостью от коллекции.

    Args:
        collection: Коллекция MongoDB (из get_activation_code_collection).

    Returns:
        ActivationCodeDAO: Data Access Object для кодов активации.
    """
    return ActivationCodeDAO(collection)


def get_activation_code_service(
    code_dao: ActivationCodeDAO = Depends(get_activation_code_dao),
) -> ActivationCodeService:
    """Создать ActivationCodeService с зависимостью.

    Args:
        code_dao: ActivationCodeDAO (из get_activation_code_dao).

    Returns:
        ActivationCodeService: Сервис для бизнес-логики кодов активации.
    """
    return ActivationCodeService(code_dao=code_dao)
