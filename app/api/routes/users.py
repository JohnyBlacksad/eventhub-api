"""User endpoints.

Модуль содержит endpoints для управления профилем пользователя:
получение, обновление, удаление.
"""

from fastapi import HTTPException, status, Depends, APIRouter
from app.schemas.users import UserResponseModel, UserUpdateModel
from app.api.deps import get_current_user
from app.services.user import UserService
from app.depency_container.users_deps import get_user_service

user_router = APIRouter(tags=['Users'])


@user_router.get('/me', response_model=UserResponseModel)
async def get_user(user: UserResponseModel = Depends(get_current_user)):
    """Получить профиль текущего пользователя.

    Args:
        user: Данные текущего пользователя (из get_current_user).

    Returns:
        UserResponseModel: Профиль пользователя.
    """
    return user


@user_router.put('/me', response_model=UserResponseModel)
async def update_user(
    update_data: UserUpdateModel,
    user: UserResponseModel = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """Обновить профиль текущего пользователя.

    Args:
        update_data: Данные для обновления (firstName, lastName, phoneNumber).
        user: Данные текущего пользователя (из get_current_user).
        user_service: Сервис пользователей.

    Returns:
        UserResponseModel: Обновлённый профиль пользователя.
    """
    updated_user = await user_service.update_user(user.id, update_data)

    return updated_user


@user_router.delete('/me', status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user: UserResponseModel = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """Удалить аккаунт текущего пользователя.

    Args:
        user: Данные текущего пользователя (из get_current_user).
        user_service: Сервис пользователей.

    Returns:
        None: Возвращает 204 No Content при успешном удалении.

    Raises:
        HTTPException: 400 если у пользователя есть активные события.
    """
    await user_service.delete_user(user.id)
    return