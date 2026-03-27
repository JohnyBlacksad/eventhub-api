"""Сервис для работы с очередями задач.

Модуль предоставляет QueueService для отправки задач в очередь из endpoint'ов приложения.
"""

from typing import Optional
from taskiq import AsyncBroker

from app.tasks.broker import broker as main_broker
from app.tasks.cleanup import delete_event_task
from app.tasks.cache import (
    invalidate_event_cache_task,
    invalidate_event_list_cache_task,
    invalidate_user_cache_task,
    invalidate_user_list_cache_task,
)
from app.tasks.notifications import (
    send_event_update_notification_task,
    send_registration_notification_task,
)

from app.utils.logger import get_trace_id

class QueueService:
    """Сервис для отправки очередей в очередь

    Attributes:
        broker: TaskIQ брокер для отправки задач.
    """

    def __init__(self, broker: AsyncBroker = main_broker):
        self.broker = broker

    async def delete_event(self, event_id: str, user_id: Optional[str] = None):
        """Отправить задачу удаления события.

        Args:
            event_id: MongoDB ObjectID события.
            user_id: MongoDB ObjectID пользователя.
        """

        await delete_event_task.kicker().with_labels(trace_id=get_trace_id()).kiq(event_id, user_id)

    async def invalidate_event_cache(self, event_id: str):
        """Отправить задачу инвалидации кэша события.

        Args:
            event_id: MongoDB ObjectID события.
        """

        await invalidate_event_cache_task.kicker().with_labels(trace_id=get_trace_id()).kiq(event_id)

    async def invalidate_event_list_cache(self):
        """Отправить задачу инвалидации кэша списка событий"""

        await invalidate_event_list_cache_task.kicker().with_labels(trace_id=get_trace_id()).kiq()

    async def invalidate_user_cache(self, user_id: str):
        """Отправить задачу инвалидации кэша пользователя

        Args:
            user_id: MongoDB ObjectID пользователя.
        """

        await invalidate_user_cache_task.kicker().with_labels(trace_id=get_trace_id()).kiq(user_id)

    async def invalidate_user_list_cache(self):
        """Отправить задачу инвалидации кэша списка пользователей"""

        await invalidate_user_list_cache_task.kicker().with_labels(trace_id=get_trace_id()).kiq()

    async def send_registration_notification(
        self,
        user_id: str,
        event_id: str,
        email: Optional[str] = None,
        phone: Optional[str] = None,
    ):
        """Отправить уведомление о регистрации.

        Args:
            user_id: MongoDB ObjectId пользователя.
            event_id: MongoDB ObjectId события.
            email: Email пользователя (опционально).
            phone: Телефон пользователя (опционально).
        """
        await send_registration_notification_task.kicker().with_labels(trace_id=get_trace_id()).kiq(
            user_id, event_id, email, phone
        )

    async def send_event_update_notification(
        self,
        user_ids: list[str],
        event_id: str,
        update_type: str,
    ):
        """Отправить уведомление об обновлении события.

        Args:
            user_ids: Список MongoDB ObjectId пользователей.
            event_id: MongoDB ObjectId события.
            update_type: Тип обновления.
        """
        await send_event_update_notification_task.kicker().with_labels(trace_id=get_trace_id()).kiq(
            user_ids, event_id, update_type
        )

def get_queue_service() -> QueueService:
    return QueueService()