"""Сервис событий.

Модуль содержит EventService для бизнес-логики событий:
создание, чтение, обновление, удаление событий и регистраций.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional

from bson import ObjectId
from fastapi import HTTPException, status

from app.config import settings
from app.models.events import EventDAO
from app.models.registration import RegistrationDAO
from app.schemas.enums.event_enums.event_enums import EventStatusEnum
from app.schemas.event import EventCreateModel, EventFilterParams, EventResponseModel, EventUpdateModel


class EventService:
    """Сервис для бизнес-логики событий.

    Использует EventDAO для CRUD операций с событиями
    и RegistrationDAO для управления регистрациями.

    Атрибуты:
        event_dao: Data Access Object для событий.
        registration_dao: Data Access Object для регистраций.
    """

    def __init__(self, event_dao: EventDAO, registration_dao: RegistrationDAO):
        """Инициализация EventService.

        Args:
            event_dao: EventDAO для CRUD операций.
            registration_dao: RegistrationDAO для регистраций.
        """
        self.event_dao = event_dao
        self.registration_dao = registration_dao

    async def create_event(self, event_data: EventCreateModel, user_id: str) -> EventResponseModel:
        """Создать новое событие.

        Args:
            event_data: Данные события для создания.
            user_id: MongoDB ObjectId создателя.

        Returns:
            EventResponseModel: Данные созданного события.

        Raises:
            HTTPException: 500 если событие не создано.
        """
        event_dict = event_data.model_dump(by_alias=True)
        event_dict["created_by"] = ObjectId(user_id)
        event_dict["created_at"] = datetime.now(timezone.utc)

        new_id = await self.event_dao.create_event(event_dict)
        raw_event = await self.event_dao.get_event(str(new_id))

        if not raw_event:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Server error. Event not created, please try again later.",
            )

        return EventResponseModel.model_validate(raw_event, from_attributes=True)

    async def get_event(self, event_id: str) -> EventResponseModel:
        """Получить событие по ID.

        Args:
            event_id: MongoDB ObjectId события.

        Returns:
            EventResponseModel: Данные события.

        Raises:
            HTTPException: 400 если ID невалиден.
            HTTPException: 404 если событие не найдено.
        """
        if not ObjectId.is_valid(event_id):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid event ID format")

        raw_event = await self.event_dao.get_event(event_id)

        if not raw_event:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

        raw_event["_id"] = str(raw_event["_id"])
        raw_event["created_by"] = str(raw_event["created_by"])

        return EventResponseModel.model_validate(raw_event, from_attributes=True)

    async def get_events(
        self, filters: Optional[EventFilterParams] = None, skip: int = 0, limit: int = 10
    ) -> list[EventResponseModel]:
        """Получить список событий с пагинацией.

        Args:
            filter: Фильтр для поиска (опционально).
            skip: Количество пропускаемых записей.
            limit: Максимальное количество записей.

        Returns:
            list[EventResponseModel]: Список событий.
        """
        raw_event_list = await self.event_dao.get_events(
            filter_obj=filters,
            skip=skip,
            limit=limit,
            sort_by=filters.sort_by if filters else "startDate",
            sort_order=filters.sort_order if filters else "asc",
        )

        result = [EventResponseModel.model_validate(event, from_attributes=True) for event in raw_event_list]

        return result

    async def update_event(self, event_id: str, user_id: str, update_data: EventUpdateModel) -> EventResponseModel:
        """Обновить данные события.

        Args:
            event_id: MongoDB ObjectId события.
            user_id: MongoDB ObjectId пользователя.
            update_data: Данные для обновления.

        Returns:
            EventResponseModel: Обновлённые данные события.

        Raises:
            HTTPException: 404 если событие не найдено.
            HTTPException: 403 если пользователь не создатель.
        """
        current_event = await self.event_dao.get_event(event_id)

        if not current_event:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

        if str(current_event["created_by"]) != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not the creator of this event")

        data = update_data.model_dump(by_alias=True, exclude_none=True)

        if "status" in data:
            new_status = data["status"]
            cleanup_seconds = settings.events_config.cleanup_sec
            death_date = datetime.now(timezone.utc) + timedelta(seconds=cleanup_seconds)
            if new_status in [EventStatusEnum.CANCELLED, EventStatusEnum.FINISHED]:
                data["deleted_at"] = death_date
                await self.registration_dao.set_deletion_time_for_event(event_id, death_date)
            else:
                data["deleted_at"] = None

        updated_event = await self.event_dao.update_event(event_id, data)

        updated_event["_id"] = str(updated_event["_id"])
        updated_event["created_by"] = str(updated_event["created_by"])

        return EventResponseModel.model_validate(updated_event, from_attributes=True)

    async def delete_event(self, event_id: str, user_id: str) -> bool:
        """Удалить событие.

        Args:
            event_id: MongoDB ObjectId события.
            user_id: MongoDB ObjectId пользователя.

        Returns:
            bool: True если событие удалено.

        Raises:
            HTTPException: 404 если событие не найдено.
            HTTPException: 403 если пользователь не создатель.
        """
        current_event = await self.event_dao.get_event(event_id)

        if not current_event:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

        if str(current_event["created_by"]) != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not the creator of this event")
        await self.registration_dao.delete_all_registrations_for_event(event_id)
        result = await self.event_dao.delete_event(event_id)
        return result

    async def delete_event_for_admin(self, event_id: str) -> bool:
        """Удалить событие администратором.

        Args:
            event_id: MongoDB ObjectId события.

        Returns:
            bool: True если событие удалено.

        Raises:
            HTTPException: 404 если событие не найдено.

        Note:
            Проверка прав администратора выполняется в endpoint.
        """
        current_event = await self.event_dao.get_event(event_id)

        if not current_event:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

        await self.registration_dao.delete_all_registrations_for_event(event_id)
        result = await self.event_dao.delete_event(event_id)
        return result

    async def register_for_event(self, event_id: str, user_id: str) -> dict:
        """Зарегистрировать пользователя на событие.

        Args:
            event_id: MongoDB ObjectId события.
            user_id: MongoDB ObjectId пользователя.

        Returns:
            dict: Статус регистрации.

        Raises:
            HTTPException: 400 если ID невалиден.
            HTTPException: 404 если событие не найдено.
            HTTPException: 400 если пользователь уже зарегистрирован.
            HTTPException: 400 если событие заполнено.
        """
        # Валидация ObjectId
        if not ObjectId.is_valid(event_id):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid event ID format")

        current_event = await self.event_dao.get_event(event_id)

        if not current_event:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

        existing = await self.registration_dao.get_existing_registration(event_id, user_id)

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="You are already registered for this event"
            )

        if current_event.get("max_participants") is not None:
            registrations = await self.registration_dao.get_event_registrations(
                event_id=event_id, skip=0, limit=current_event["max_participants"] + 1
            )

            if len(registrations) >= current_event["max_participants"]:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Event is full")

        await self.registration_dao.add_registration(event_id, user_id)

        return {"status": "registered", "event_id": event_id}

    async def unregister_from_event(self, event_id: str, user_id: str) -> dict:
        """Отменить регистрацию пользователя на событие.

        Args:
            event_id: MongoDB ObjectId события.
            user_id: MongoDB ObjectId пользователя.

        Returns:
            dict: Статус отмены регистрации.

        Raises:
            HTTPException: 400 если ID невалиден.
            HTTPException: 404 если событие не найдено.
            HTTPException: 404 если регистрация не найдена.
        """
        # Валидация ObjectId
        if not ObjectId.is_valid(event_id):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid event ID format")

        current_event = await self.event_dao.get_event(event_id)

        if not current_event:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

        result = await self.registration_dao.remove_registration(event_id, user_id)

        if not result:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Registration not found")

        return {"status": "unregistered", "event_id": event_id}

    async def get_event_participants(self, event_id: str, skip: int = 0, limit: int = 50) -> list[dict]:
        """Получить список участников события.

        Args:
            event_id: MongoDB ObjectId события.
            skip: Количество пропускаемых записей.
            limit: Максимальное количество записей.

        Returns:
            list[dict]: Список регистраций участников.

        Raises:
            HTTPException: 400 если ID невалиден.
            HTTPException: 404 если событие не найдено.
        """
        # Валидация ObjectId
        if not ObjectId.is_valid(event_id):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid event ID format")

        current_event = await self.event_dao.get_event(event_id)

        if not current_event:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

        participants = await self.registration_dao.get_event_registrations(event_id=event_id, skip=skip, limit=limit)

        # Конвертируем ObjectId в строку для сериализации
        for p in participants:
            if "_id" in p:
                p["_id"] = str(p["_id"])
            if "event_id" in p:
                p["event_id"] = str(p["event_id"])
            if "user_id" in p:
                p["user_id"] = str(p["user_id"])

        return participants

    async def get_user_registrations(self, user_id: str) -> list[dict]:
        """Получить список регистраций пользователя.

        Args:
            user_id: MongoDB ObjectId пользователя.

        Returns:
            list[dict]: Список регистраций пользователя.
        """
        registrations = await self.registration_dao.get_user_registrations(user_id)

        # Конвертируем ObjectId в строку для сериализации
        for r in registrations:
            if "_id" in r:
                r["_id"] = str(r["_id"])
            if "event_id" in r:
                r["event_id"] = str(r["event_id"])
            if "user_id" in r:
                r["user_id"] = str(r["user_id"])

        return registrations

    async def delete_all_user_events_and_registrations(self, user_id: str) -> bool:
        """Удалить все события и регистрации пользователя (cascade удаление).

        Используется при удалении пользователя администратором для очистки
        всех связанных данных пользователя.

        Args:
            user_id: MongoDB ObjectId пользователя.

        Returns:
            bool: True если все события и регистрации удалены.
        """
        is_registrations_deleted = await self.registration_dao.delete_registration_by_user(user_id)
        is_events_deleted = await self.event_dao.delete_events_by_user(user_id)

        if is_registrations_deleted and is_events_deleted:
            return True
        return False
