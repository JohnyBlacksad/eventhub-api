from fastapi import Depends
from app.database import db_client
from app.models.user import UserDAO
from app.services.auth import AuthService
from app.services.user import UserService



def get_user_collections():
    return db_client.get_db()['users'] # type: ignore


def get_user_dao(collection=Depends(get_user_collections)) -> UserDAO:
    return UserDAO(collection)


def get_auth_service() -> AuthService:
    return AuthService()


def get_user_service(
    dao: UserDAO = Depends(get_user_dao),
    auth: AuthService = Depends(get_auth_service)
) -> UserService:
    return UserService(user_dao=dao, auth_service=auth)