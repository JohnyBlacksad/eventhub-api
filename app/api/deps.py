"""Зависимости API.

Модуль содержит зависимости для аутентификации пользователей
через JWT токены.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.schemas.enums.user_enums.users_status import UserRoleEnum
from app.dependency_container.users_deps import (
    get_auth_service,
    get_user_service
)
from app.schemas.users import UserResponseModel
from app.services.auth import AuthService
from app.services.user import UserService

oauth2_scheme = HTTPBearer()


async def get_current_user(
        token: HTTPAuthorizationCredentials = Depends(oauth2_scheme),
        auth_service: AuthService = Depends(get_auth_service),
        user_service: UserService = Depends(get_user_service),
):
    """Получить текущего пользователя из JWT токена.

    Извлекает токен из заголовка Authorization, декодирует его
    и находит пользователя в базе данных.

    Args:
        token: JWT токен из заголовка Authorization.
        auth_service: Сервис аутентификации.
        user_service: Сервис пользователей.

    Returns:
        UserResponseModel: Данные текущего пользователя.

    Raises:
        HTTPException: 401 если токен невалиден или истёк.
        HTTPException: 404 если пользователь не найден.
    """
    payload = await auth_service.decode_token(token.credentials)

    user_id = payload.get('user_id')
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid token payload'
        )

    user = await user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='User not found'
        )

    return user

async def require_role(
        current_user: UserResponseModel = Depends(get_current_user)):

    if current_user.role not in (UserRoleEnum.ORGANIZER, UserRoleEnum.ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f'Role {current_user.role} is not allowed.'
        )

    return current_user

async def require_admin(
        current_user: UserResponseModel = Depends(get_current_user)):

    if current_user.role != UserRoleEnum.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Admin access required'
        )

    return current_user