"""Задачи для управления кэшем.

Модуль содержит фоновые задачи для инвалидации кэша.
"""

from app.services.cache import cache_service
from app.tasks.broker import broker
from app.tasks.settings import TaskQueueSettings

from app.utils.logger import get_logger
from app.config_models.loggers_enum import LoggerName

logger = get_logger(LoggerName.QUEUE_TASK_CACHE_LOGGER)

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
    try:
        await cache_service.delete_event(event_id)

        return {
            "status": "success",
            "event_id": event_id,
            "cache_invalidated": True
        }
    except Exception as e:
        logger.warning("Invalidate event cache task error", extra={
            "event_id": event_id,
            "error": str(e),
        })
        raise


@cache_task
async def invalidate_event_list_cache_task() -> dict:
    """Инвалидировать весь кэш списка событий

    Returns:
        dict: Результат инвалидации.

    Raises:
        Exception: При ошибке подключения к Redis.
    """
    try:
        await cache_service.delete_event_list()

        return {
            "status": "success",
            "cache_invalidated": True
        }
    except Exception as e:
        logger.warning("Invalidate event list cache task error", extra={
            "error": str(e),
        })
        raise

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
    try:
        await cache_service.delete_user(user_id)

        return {
            "status": "success",
            "user_id": user_id,
            "cache_invalidated": True
        }
    except Exception as e:
        logger.warning("Invalidate user cache task error", extra={
            "user_id": user_id,
            "error": str(e)
        })
        raise

@cache_task
async def invalidate_user_list_cache_task() -> dict:
    """Инвалидировать весь кэш списка пользователей.

    Returns:
        dict: Результат инвалидации кэша.

    Raises:
        Exception: При ошибке подключения к Redis.
    """
    try:
        await cache_service.delete_user_list()

        return {
            "status": "success",
            "cache_invalidated": True
        }
    except Exception as e:
        logger.warning("Invalidate user list cache task", extra={
            "error": str(e),
        })
        raise