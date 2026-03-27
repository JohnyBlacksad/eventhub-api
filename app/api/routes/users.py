"""User endpoints.

Модуль содержит endpoints для управления профилем пользователя:
получение, обновление, удаление.
"""

from fastapi import APIRouter, Depends, status

from app.api.deps import get_current_user
from app.dependency_container.users_deps import get_user_service
from app.schemas.users import UserResponseModel, UserUpdateModel
from app.services.queue import QueueService, get_queue_service
from app.services.user import UserService

user_router = APIRouter(tags=["Users"])


@user_router.get("/me", response_model=UserResponseModel)
async def get_user(user: UserResponseModel = Depends(get_current_user)):
    """Получить профиль текущего пользователя.

    Args:
        user: Данные текущего пользователя (из get_current_user).

    Returns:
        UserResponseModel: Профиль пользователя.
    """
    return user


@user_router.put("/me", response_model=UserResponseModel)
async def update_user(
    update_data: UserUpdateModel,
    user: UserResponseModel = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
    queue_service: QueueService = Depends(get_queue_service),
):
    """Обновить профиль текущего пользователя.

    Args:
        update_data: Данные для обновления (firstName, lastName, phoneNumber).
        user: Данные текущего пользователя (из get_current_user).
        user_service: Сервис пользователей.
        queue_service: Сервис очередей.

    Returns:
        UserResponseModel: Обновлённый профиль пользователя.
    """
    updated_user = await user_service.update_user(user.id, update_data)

    await queue_service.invalidate_user_cache(str(user.id))
    await queue_service.invalidate_user_list_cache()

    return updated_user


@user_router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user: UserResponseModel = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
    queue_service: QueueService = Depends(get_queue_service),
):
    """Удалить аккаунт текущего пользователя.

    Args:
        user: Данные текущего пользователя (из get_current_user).
        user_service: Сервис пользователей.
        queue_service: Сервис очередей.

    Returns:
        None: Возвращает 204 No Content при успешном удалении.

    Raises:
        HTTPException: 400 если у пользователя есть активные события.
    """
    await user_service.delete_user(user.id)

    await queue_service.invalidate_user_cache(str(user.id))
    await queue_service.invalidate_user_list_cache()

    return


@user_router.post("/upgrade", response_model=UserResponseModel)
async def upgrade_role(
    code: str,
    current_user: UserResponseModel = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
    queue_service: QueueService = Depends(get_queue_service),
):
    """Повысить роль текущего пользователя используя код активации.

    Принимает код активации от администратора и повышает роль пользователя
    до ORGANIZER (или другой роли указанной в коде).

    Args:
        code: Строка кода активации.
        current_user: Данные текущего пользователя (из get_current_user).
        user_service: Сервис пользователей.
         queue_service: Сервис очередей.

    Returns:
        UserResponseModel: Обновлённые данные пользователя с новой ролью.

    Raises:
        HTTPException: 403 если код невалиден, истёк или уже использован.
        HTTPException: 404 если пользователь не найден.
    """

    updated_user = await user_service.upgrade_role(user_id=str(current_user.id), code_str=code)

    await queue_service.invalidate_user_cache(str(current_user.id))
    await queue_service.invalidate_user_list_cache()

    return updated_user
