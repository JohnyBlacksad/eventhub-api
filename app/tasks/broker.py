"""Модуль создает и настраивает Redis брокер для очередей и задач."""

from taskiq import AsyncBroker, TaskiqEvents
from taskiq_redis import ListQueueBroker
from app.database import db_client
from app.redis_client import redis_client
from app.config import settings
from app.tasks.settings import TaskQueueSettings


class TaskIQBroker:
    """Управление брокером задач"""

    _instance: AsyncBroker | None = None

    @classmethod
    def get_broker(cls) -> AsyncBroker:
        """Получить инстанс брокера"""

        if cls._instance is None:
            cls._instance = cls._create_broker(TaskQueueSettings.QUEUE_MAIN)

        return cls._instance

    @classmethod
    def _create_broker(cls, queue_name: str) -> AsyncBroker:
        url = settings.redis_config.url or "redis://redis:6379"

        broker = ListQueueBroker(
            url=url,
            queue_name=queue_name,
        )

        @broker.on_event(TaskiqEvents.WORKER_STARTUP)
        async def startup(state):
            """Инициализация подключений при старте воркера."""
            await redis_client.connect()
            await db_client.connect()

        @broker.on_event(TaskiqEvents.WORKER_SHUTDOWN)
        async def shutdown(state):
            """Закрытие подключений при остановке воркера."""
            await redis_client.close()
            await db_client.close()

        return broker

broker = TaskIQBroker.get_broker()

from app.tasks.cleanup import delete_event_task  # noqa: F401
from app.tasks.notifications import (  # noqa: F401
    send_registration_notification_task,
    send_event_update_notification_task,
)
from app.tasks.cache import (  # noqa: F401
    invalidate_event_cache_task,
    invalidate_event_list_cache_task,
    invalidate_user_cache_task,
    invalidate_user_list_cache_task,
)