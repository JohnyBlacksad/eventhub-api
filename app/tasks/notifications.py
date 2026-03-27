"""Задачи для уведомлений.

Модуль содержит фоновые задачи для отправки email/SMS уведомлений.
"""

from typing import Optional
from app.tasks.broker import broker
from app.tasks.settings import TaskQueueSettings

notification_task = broker.task(
    #queue_name=TaskQueueSettings.QUEUE_NOTIFICATION,
    timeout=TaskQueueSettings.NOTIFICATION_TIMEOUT,
    max_retries=TaskQueueSettings.MAX_RETRIES,
    retry_delay=TaskQueueSettings.RETRY_DELAY
)

@notification_task
async def send_registration_notification_task(
    user_id: str,
    event_id: str,
    email: Optional[str] = None,
    phone: Optional[str] = None,
) -> dict:
    """Отправить уведомление о регистрации на событие.

    Args:
        user_id: MongoDB ObjectID пользователя.
        event_id: MongoDB ObjectID события.
        email: Email пользователя.
        phone: Телефон пользователя.

    Returns:
        dict: Результат отправки.

    Raises:
        Exception: При ошибке отправки уведомления.
    """

    # TODO: Реализовать отправку email/SMS

    result = {
        "status": "success",
        "user_id": user_id,
        "event_id": event_id,
        "notification_sent": False # TODO: Заменить на True после реализации.
    }

    return result


@notification_task
async def send_event_update_notification_task(
    user_ids: list[str],
    event_id: str,
    update_type: str,
) -> dict:
    """
    Отправить уведомление об обновлении события.

    Args:
        user_id: Список MongoDB ObjectID пользователей.
        event_id: MongoDB ObjectID события.
        update_type: Тип обновления (canceled, finished, etc)

    Returns:
        dict: Результат отправки.

    Raises:
        Exception: При ошибке отправки уведомления.
    """

    # TODO: Реализовать массовую рассылку.

    result = {
        "status": "success",
        "event_id": event_id,
        "update_type": update_type,
        "recipients_count": len(user_ids),
        "notifications_sent": 0, # TODO: заменить после реализации.
    }

    return result