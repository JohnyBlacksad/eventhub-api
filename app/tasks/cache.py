"""Задачи для управления кэшем.

Модуль содержит фоновые задачи для инвалидации кэша.
"""

from app.services.cache import cache_service
from app.tasks.broker import broker
from app.tasks.settings import TaskQueueSettings

cache_task = broker.task(
    #queue_name=TaskQueueSettings.QUEUE_CACHE,
    timeout=TaskQueueSettings.CACHE_TIMEOUT,
    max_retries=TaskQueueSettings.MAX_RETRIES,
    retry_delay=TaskQueueSettings.RETRY_DELAY,
)

@cache_task
async def invalidate_event_cache_task(event_id: str) -> dict:
    """
    Инвалидировать кэш события.

    Args:
        event_id: MongoDB ObjectID события.

    Returns:
        dict: Результат инвалидации.

    Raises:
        Exception: При ошибке подключения к Redis.
    """

    await cache_service.delete_event(event_id)

    return {
        "status": "success",
        "event_id": event_id,
        "cache_invalidated": True
    }


@cache_task
async def invalidate_event_list_cache_task() -> dict:
    """Инвалидировать весь кэш списка событий

    Returns:
        dict: Результат инвалидации.

    Raises:
        Exception: При ошибке подключения к Redis.
    """

    await cache_service.delete_event_list()

    return {
        "status": "success",
        "cache_invalidated": True
    }

@cache_task
async def invalidate_user_cache_task(user_id: str) -> dict:
    """Инвалидировать кэш пользователя.

    Args:
        user_id: MongoDB ObjectID пользователя.

    Returns:
        dict: Результат инвалидации кэша.

    Raises:
        Exception: При ошибке подключения к Redis.
    """

    await cache_service.delete_user(user_id)

    return {
        "status": "success",
        "user_id": user_id,
        "cache_invalidated": True
    }

@cache_task
async def invalidate_user_list_cache_task() -> dict:
    """Инвалидировать весь кэш списка пользователей.

    Returns:
        dict: Результат инвалидации кэша.

    Raises:
        Exception: При ошибке подключения к Redis.
    """

    await cache_service.delete_user_list()

    return {
        "status": "success",
        "cache_invalidated": True
    }