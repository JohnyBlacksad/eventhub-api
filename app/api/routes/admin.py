"""Admin endpoints.

Модуль содержит endpoints для администрирования:
управление пользователями (ban/unban), кодами активации, событиями.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.api.deps import require_admin
from app.dependency_container.activation_code_deps import get_activation_code_service
from app.dependency_container.event_deps import get_event_service
from app.schemas.activation_code import ActivationCodeCreateModel, ActivationCodeModelResponse, CodeFiltersResponse, GetActivationCodesResponseModel
from app.schemas.event import EventFilterParams, GetEventsModel
from app.schemas.users import GetUsersResponseModel, UserFilterModel, UserResponseModel
from app.dependency_container.users_deps import get_user_service
from app.services.activation_code import ActivationCodeService
from app.services.event import EventService
from app.services.user import UserService

admin_route = APIRouter(tags=['Admin'])


@admin_route.put('/users/{user_id}/ban', response_model=UserResponseModel, status_code=status.HTTP_200_OK)
async def ban_user(
    user_id: str,
    current_user: UserResponseModel = Depends(require_admin),
    user_service: UserService = Depends(get_user_service)
):
    """Забанить пользователя (только ADMIN).

    Args:
        user_id: MongoDB ObjectId пользователя.
        current_user: Текущий пользователь (ADMIN).
        user_service: Сервис пользователей.

    Returns:
        UserResponseModel: Обновлённые данные пользователя.
    """
    return await user_service.set_ban_user(user_id=user_id, is_banned=True)


@admin_route.put('/users/{user_id}/unban', response_model=UserResponseModel, status_code=status.HTTP_200_OK)
async def unban_user(
    user_id: str,
    current_user: UserResponseModel = Depends(require_admin),
    user_service: UserService = Depends(get_user_service)
):
    """Разбанить пользователя (только ADMIN).

    Args:
        user_id: MongoDB ObjectId пользователя.
        current_user: Текущий пользователь (ADMIN).
        user_service: Сервис пользователей.

    Returns:
        UserResponseModel: Обновлённые данные пользователя.
    """
    return await user_service.set_ban_user(user_id=user_id, is_banned=False)


@admin_route.post('/activation-code', response_model=ActivationCodeModelResponse, status_code=status.HTTP_201_CREATED)
async def create_activation_code(
    request: ActivationCodeCreateModel,
    current_user: UserResponseModel = Depends(require_admin),
    service: ActivationCodeService = Depends(get_activation_code_service)
):
    """Создать код активации (только ADMIN).

    Args:
        request: Данные для создания кода (role, code).
        current_user: Текущий пользователь (ADMIN).
        service: Сервис кодов активации.

    Returns:
        ActivationCodeModelResponse: Данные созданного кода.
    """
    return await service.create_code(role=request.role, code=request.code)


@admin_route.get('/activation-codes', response_model=GetActivationCodesResponseModel, status_code=status.HTTP_200_OK)
async def get_activation_codes(
    filters: CodeFiltersResponse = Depends(),
    skip: int = 0,
    limit: int = 100,
    current_user: UserResponseModel = Depends(require_admin),
    service: ActivationCodeService = Depends(get_activation_code_service)
):
    """Получить список кодов активации с пагинацией (только ADMIN).

    Args:
        filters: Фильтры для поиска (is_used, role, created_at, activated_at).
        skip: Количество пропускаемых записей.
        limit: Максимальное количество записей.
        current_user: Текущий пользователь (ADMIN).
        service: Сервис кодов активации.

    Returns:
        GetActivationCodesResponseModel: Список кодов.
    """
    return await service.get_codes(
        skip=skip,
        limit=limit,
        filters=filters
    )


@admin_route.delete('/activation-code/{code_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_activation_code(
    code_id: str,
    current_user: UserResponseModel = Depends(require_admin),
    service: ActivationCodeService = Depends(get_activation_code_service)
):
    """Удалить код активации по ID (только ADMIN).

    Args:
        code_id: MongoDB ObjectId кода.
        current_user: Текущий пользователь (ADMIN).
        service: Сервис кодов активации.

    Returns:
        None: Возвращает 204 No Content при успешном удалении.
    """
    await service.delete_code(code_id=code_id)


@admin_route.get('/users', response_model=GetUsersResponseModel, status_code=status.HTTP_200_OK)
async def get_all_users(
    skip: int = 0,
    limit: int = 100,
    filters: UserFilterModel = Depends(),
    current_user: UserResponseModel = Depends(require_admin),
    service: UserService = Depends(get_user_service)
):
    """Получить список всех пользователей с пагинацией и фильтрами (только ADMIN).

    Args:
        skip: Количество пропускаемых записей.
        limit: Максимальное количество записей.
        filters: Фильтры для поиска (role, is_banned, created_at, created_at_to).
        current_user: Текущий пользователь (ADMIN).
        service: Сервис пользователей.

    Returns:
        GetUsersResponseModel: Список пользователей.
    """
    return await service.get_users(
        skip=skip,
        limit=limit,
        filter_obj=filters.model_dump()
    )


@admin_route.get('/events', response_model=GetEventsModel, status_code=status.HTTP_200_OK)
async def get_all_events(
    filters: EventFilterParams = Depends(),
    skip: int = 0,
    limit: int = 100,
    current_user: UserResponseModel = Depends(require_admin),
    service: EventService = Depends(get_event_service)
):
    """Получить список всех событий с пагинацией и фильтрами (только ADMIN).

    Args:
        filters: Фильтры для поиска (status, city, country, date_from, date_to, search).
        skip: Количество пропускаемых записей.
        limit: Максимальное количество записей.
        current_user: Текущий пользователь (ADMIN).
        service: Сервис событий.

    Returns:
        GetEventsModel: Список событий.
    """
    events = await service.get_events(
        filters=filters,
        skip=skip,
        limit=limit
    )
    return GetEventsModel(events=events)


@admin_route.delete('/events/{event_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_event_admin(
    event_id: str,
    current_user: UserResponseModel = Depends(require_admin),
    service: EventService = Depends(get_event_service)
):
    """Удалить событие по ID (только ADMIN).

    Args:
        event_id: MongoDB ObjectId события.
        current_user: Текущий пользователь (ADMIN).
        service: Сервис событий.

    Returns:
        None: Возвращает 204 No Content при успешном удалении.
    """
    await service.delete_event_for_admin(event_id=event_id)


@admin_route.delete('/users/{user_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_admin(
    user_id: str,
    current_user: UserResponseModel = Depends(require_admin),
    user_service: UserService = Depends(get_user_service),
    event_service: EventService = Depends(get_event_service)
):
    """Удалить пользователя и все связанные данные (только ADMIN).

    Args:
        user_id: MongoDB ObjectId пользователя.
        current_user: Текущий пользователь (ADMIN).
        user_service: Сервис пользователей.
        event_service: Сервис событий.

    Returns:
        None: Возвращает 204 No Content при успешном удалении.
    """
    user = await user_service.get_user_by_id(str(user_id))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='User not found'
        )


    await event_service.delete_all_user_events_and_registrations(str(user_id))

    is_deleted = await user_service.delete_user_by_admin(str(user_id))
    if not is_deleted:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Failed to delete user'
        )