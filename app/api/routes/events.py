"""Event endpoints.

Модуль содержит endpoints для управления событиями:
создание, чтение, обновление, удаление, регистрация на события.
"""

from fastapi import Depends, APIRouter, Query, status
from app.schemas.users import UserResponseModel
from app.schemas.event import EventFilterParams, EventResponseModel, EventCreateModel, GetEventsModel, EventUpdateModel
from app.services.event import EventService
from app.api.deps import require_role, get_current_user
from app.dependency_container.event_deps import get_event_service

event_router = APIRouter(tags=['Events'])


@event_router.post('/', response_model=EventResponseModel, status_code=status.HTTP_201_CREATED)
async def create_event(event_data: EventCreateModel,
                       current_user: UserResponseModel = Depends(require_role),
                       event_service: EventService = Depends(get_event_service)):
    """Создать новое событие (только ORGANIZER или ADMIN).

    Args:
        event_data: Данные события для создания.
        current_user: Текущий пользователь (ORGANIZER или ADMIN).
        event_service: Сервис событий.

    Returns:
        EventResponseModel: Данные созданного события.
    """
    response = await event_service.create_event(
        event_data=event_data, user_id=str(current_user.id))

    return response


@event_router.get('/', response_model=GetEventsModel, status_code=status.HTTP_200_OK)
async def get_events(
    filters: EventFilterParams = Depends(),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, le=100),
    event_service: EventService = Depends(get_event_service),
):
    """Получить список событий с пагинацией и фильтрами.

    Args:
        filters: Фильтры для поиска (status, city, country, date_from, date_to, search).
        skip: Количество пропускаемых записей.
        limit: Максимальное количество записей.
        event_service: Сервис событий.

    Returns:
        GetEventsModel: Список событий.
    """
    response = await event_service.get_events(filters=filters, skip=skip, limit=limit)

    return GetEventsModel(events=response)


@event_router.get('/{event_id}', response_model=EventResponseModel, status_code=status.HTTP_200_OK)
async def get_event(event_id: str, event_service: EventService = Depends(get_event_service)):
    """Получить одно событие по ID.

    Args:
        event_id: MongoDB ObjectId события.
        event_service: Сервис событий.

    Returns:
        EventResponseModel: Данные события.
    """
    response = await event_service.get_event(event_id)
    return response


@event_router.put('/{event_id}', response_model=EventResponseModel, status_code=status.HTTP_200_OK)
async def update_event(
    event_id: str,
    update_data: EventUpdateModel,
    event_service: EventService = Depends(get_event_service),
    current_user: UserResponseModel = Depends(require_role)
):
    """Обновить данные события (только создатель или ADMIN).

    Args:
        event_id: MongoDB ObjectId события.
        update_data: Данные для обновления.
        event_service: Сервис событий.
        current_user: Текущий пользователь (создатель или ADMIN).

    Returns:
        EventResponseModel: Обновлённые данные события.
    """
    response = await event_service.update_event(
        event_id=event_id,
        user_id=str(current_user.id),
        update_data=update_data
    )

    return response


@event_router.delete('/{event_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(
    event_id: str,
    event_service: EventService = Depends(get_event_service),
    current_user: UserResponseModel = Depends(require_role)
):
    """Удалить событие (только создатель или ADMIN).

    Args:
        event_id: MongoDB ObjectId события.
        event_service: Сервис событий.
        current_user: Текущий пользователь (создатель или ADMIN).

    Returns:
        None: Возвращает 204 No Content при успешном удалении.
    """
    response = await event_service.delete_event(
        event_id=event_id,
        user_id=str(current_user.id)
    )


@event_router.post('/{event_id}/register', status_code=status.HTTP_201_CREATED)
async def register_for_event(
    event_id: str,
    event_service: EventService = Depends(get_event_service),
    current_user: UserResponseModel = Depends(get_current_user)
):
    """Зарегистрировать текущего пользователя на событие.

    Args:
        event_id: MongoDB ObjectId события.
        event_service: Сервис событий.
        current_user: Текущий пользователь.

    Returns:
        dict: Статус регистрации.
    """
    response = await event_service.register_for_event(
        event_id=event_id,
        user_id=str(current_user.id)
    )


@event_router.delete('/{event_id}/register', status_code=status.HTTP_200_OK)
async def delete_registration(
    event_id: str,
    event_service: EventService = Depends(get_event_service),
    current_user: UserResponseModel = Depends(get_current_user)
):
    """Отменить регистрацию текущего пользователя на событие.

    Args:
        event_id: MongoDB ObjectId события.
        event_service: Сервис событий.
        current_user: Текущий пользователь.

    Returns:
        dict: Статус отмены регистрации.
    """
    response = await event_service.unregister_from_event(
        event_id=event_id,
        user_id=str(current_user.id)
    )


@event_router.get('/{event_id}/participants', response_model=list[dict], status_code=status.HTTP_200_OK)
async def get_event_participants(
    event_id: str,
    skip=Query(0, ge=0),
    limit=Query(10, le=50),
    event_service: EventService = Depends(get_event_service)
):
    """Получить список участников события с пагинацией.

    Args:
        event_id: MongoDB ObjectId события.
        skip: Количество пропускаемых записей.
        limit: Максимальное количество записей.
        event_service: Сервис событий.

    Returns:
        list[dict]: Список регистраций участников.
    """
    response = await event_service.get_event_participants(
        event_id=event_id,
        skip=skip,
        limit=limit
    )

    return response


@event_router.get('/registrations/me', response_model=list[dict], status_code=status.HTTP_200_OK)
async def get_my_registrations(
    current_user: UserResponseModel = Depends(get_current_user),
    event_service: EventService = Depends(get_event_service),
):
    """Получить список регистраций текущего пользователя.

    Args:
        current_user: Текущий пользователь.
        event_service: Сервис событий.

    Returns:
        list[dict]: Список регистраций пользователя.
    """
    response = await event_service.get_user_registrations(
        user_id=str(current_user.id)
    )

    return response