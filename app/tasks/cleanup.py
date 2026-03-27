"""Задачи для очистки данных.

Модуль содержит фоновые задачи для удаления событий
и очистки устаревших данных.
"""

from datetime import datetime, timezone

from app.database import db_client
from app.models.events import EventDAO
from app.models.registration import RegistrationDAO
from app.schemas.enums.event_enums.event_enums import EventStatusEnum
from app.tasks.broker import broker
from app.tasks.settings import TaskQueueSettings


cleanup_task = broker.task(
    timeout=TaskQueueSettings.CLEANUP_TIMEOUT,
    max_retries=TaskQueueSettings.MAX_RETRIES,
    retry_delay=TaskQueueSettings.RETRY_DELAY,
)


@cleanup_task
async def delete_event_task(event_id: str, user_id: str | None = None) -> dict:
    """Удалить событие (фоновая задача).

    Удаляет регистрации и помечает событие на удаление (deleted_at).
    MongoDB TTL индекс автоматически удалит событие через N секунд.

    Args:
        event_id: MongoDB ObjectId события.
        user_id: MongoDB ObjectId пользователя (опционально, для проверок).

    Returns:
        dict: Результат удаления.

    Raises:
        Exception: При ошибке подключения к БД или выполнения операции.
    """
    # Проверяем что клиент подключён
    if db_client.client is None:
        await db_client.connect()

    db = db_client.get_db()

    events_collection = db["events"]
    registrations_collection = db["registrations"]

    event_dao = EventDAO(events_collection)
    registration_dao = RegistrationDAO(registrations_collection)

    event = await event_dao.get_event(event_id)

    if not event:
        raise ValueError(f"Event not found: {event_id}")

    if user_id and str(event.get("created_by")) != user_id:
        raise PermissionError(f"Permission denied for user: {user_id}")

    await registration_dao.delete_all_registrations_for_event(event_id)

    await event_dao.update_event(event_id, {
        "status": EventStatusEnum.CANCELLED.value,
        "deleted_at": datetime.now(timezone.utc)
    })

    return {
        "status": "success",
        "event_id": event_id,
        "marked_for_deletion": True
    }