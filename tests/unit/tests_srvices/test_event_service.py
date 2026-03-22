"""Тесты на EventService — бизнес-логика событий.

Модуль содержит тесты для покрытия всех методов EventService:
- create_event() — создание события
- get_event() — получение по ID
- get_events() — список с фильтрами
- update_event() — обновление
- delete_event() — удаление
- register_for_event() — регистрация
- unregister_from_event() — отмена регистрации
- get_event_participants() — участники
- get_user_registrations() — мои регистрации
"""

from datetime import datetime, timedelta, timezone

import allure
import pytest
from fastapi import HTTPException
from app.config import settings
from app.schemas.event import EventFilterParams, EventUpdateModel
from tests.core.event_data_factory.fake_event_data import event_faker
from app.schemas.enums.event_enums.event_enums import EventStatusEnum
from app.services.event import EventService
from tests.core.const.mark_enums import (
    FeaturesEventMark,
    MarkTests,
    ModuleMarks,
    ServicesMark,
    tag,
)


@tag(MarkTests.UNITS)
@tag(ModuleMarks.SERVICES)
@tag(ServicesMark.EVENTS)
@pytest.mark.asyncio
class TestEventService:
    """Тесты для EventService."""

    @allure.title('Создание ивента с корректными данными')
    @tag(FeaturesEventMark.CREATE_EVENT)
    async def test_create_event_by_user(self, event_service: EventService, created_user):

        user, *_ = created_user

        event_data = event_faker.get_create_event_model()

        with allure.step('Запрос на создание ивента'):
            created_event = await event_service.create_event(event_data, user.id)

        with allure.step('Проверка что id владельца ивента совпадает с ID создателя ивента'):
            assert created_event.created_by == user.id

        with allure.step('Проверка данных созданного ивента'):
            assert created_event.id
            assert created_event.created_at
            assert created_event.title == event_data.title
            assert created_event.description == event_data.description
            assert created_event.max_participants == event_data.max_participants
            assert created_event.start_date.timestamp() == pytest.approx(event_data.start_date.timestamp(), abs=1)
            assert created_event.end_date.timestamp() == pytest.approx(event_data.end_date.timestamp(), abs=1) # type: ignore
            assert created_event.location == event_data.location

    @allure.title('Создание ивента фейковым пользователем')
    @tag(FeaturesEventMark.CREATE_EVENT)
    async def test_create_event_by_fake_user(self, event_service: EventService):

        user_id = event_faker.generate_random_id()

        event_data = event_faker.get_create_event_model()

        with allure.step('Запрос на создание ивента'):
            created_event = await event_service.create_event(event_data, user_id)

        with allure.step('Проверка что id владельца ивента совпадает с id создателя ивента'):
            assert created_event.created_by == user_id

        with allure.step('Проверка данных созданного ивента'):
            assert created_event.title == event_data.title
            assert created_event.description == event_data.description
            assert created_event.max_participants == event_data.max_participants
            assert created_event.start_date.timestamp() == pytest.approx(event_data.start_date.timestamp(), abs=1)
            assert created_event.end_date.timestamp() == pytest.approx(event_data.end_date.timestamp(), abs=1) # type: ignore
            assert created_event.location == event_data.location


    @allure.title('Попытка создания ивента с поломаной БД')
    @tag(FeaturesEventMark.CREATE_EVENT)
    async def test_create_event_with_breking_data_base(self, event_service: EventService, created_user, monkeypatch):

        user, *_ = created_user

        event_data = event_faker.get_create_event_model()

        async def mock_get_event(event_id):
            return None

        monkeypatch.setattr(event_service.event_dao, 'get_event', mock_get_event)

        with allure.step('Попытка создания ивента со сломаной БД'):
            with pytest.raises(HTTPException) as err:
                await event_service.create_event(event_data, user.id)

            assert err.value.status_code == 500
            assert 'Server error' in err.value.detail

    @allure.title('Получение существующего события по ID')
    @tag(FeaturesEventMark.GET_EVENT)
    async def test_get_event_success(self, event_service: EventService, created_user_with_event):
        _, event = created_user_with_event

        with allure.step('Запрос на получение ивента по ID'):
            event_data = await event_service.get_event(event.id)

        with allure.step('Проверка вернувшихся данных'):
            assert event_data.id == event.id
            assert event_data.created_at == event.created_at
            assert event_data.created_by == event.created_by
            assert event_data.title == event.title
            assert event_data.description == event.description
            assert event_data.start_date.timestamp() == pytest.approx(event.start_date.timestamp())
            assert event_data.end_date.timestamp() == pytest.approx(event.end_date.timestamp()) # type: ignore
            assert event_data.location == event.location

    @allure.title('Получение несуществующего события')
    @tag(FeaturesEventMark.GET_EVENT)
    async def test_get_event_not_found(self, event_service: EventService):

        event_id = event_faker.generate_random_id()

        with allure.step('Проверка возбуждения ошибки при попытке передачи несуществующего id'):
            with pytest.raises(HTTPException) as err:
                await event_service.get_event(event_id)

            assert err.value.status_code == 404
            assert 'not found' in err.value.detail

    @pytest.mark.parametrize(
            'invalid_data',
            [
                (1, 2, 'asd'),
                {
                    'name': 'name',
                },
                None,
                set(),
                1 == 1,
                1 != 1,
                ['one', 2, 'three']
            ],
            ids=[
                'tuple_obj',
                'dict',
                'None Type',
                'Set',
                'bool True',
                'bool False',
                'list'
            ]
            )
    @allure.title('Получение события с невалидным ObjectId')
    @tag(FeaturesEventMark.GET_EVENT)
    async def test_get_event_invalid_id(self, event_service: EventService, invalid_data):

        event_id = invalid_data

        with allure.step('Проверка возбуждения ошибки при попытке передачи невалидного ID'):
            with pytest.raises(HTTPException) as err:
                await event_service.get_event(event_id) # type: ignore

            assert err.value.status_code == 400
            assert 'Invalid event ID format' in err.value.detail

    @allure.title('Получение пустого списка событий.')
    @tag(FeaturesEventMark.GET_EVENTS)
    async def test_get_events_empty_list(self, event_service: EventService):

        with allure.step('Запрос на получения списка событий в пустую БД'):
            event_list = await event_service.get_events()

        with allure.step('Проверка на отсуствие элементов в списке'):
            assert not event_list

    @allure.title('Получение списка событий с данными')
    @tag(FeaturesEventMark.GET_EVENTS)
    async def test_get_events_with_data(self, event_service: EventService, event_factory_for_user, subtests):

        expected_events = event_factory_for_user

        with allure.step('Запрос на получение списка событий'):
            event_list = await event_service.get_events()

        with allure.step('Проверка списка событий'):
            assert len(event_list) == len(expected_events)

            sorted_actual = sorted(event_list, key=lambda e: e.id)
            sorted_expected = sorted(expected_events, key=lambda e: e.id)

            for i, (actual, expected) in enumerate(zip(sorted_actual, sorted_expected)):
                with subtests.test(msg=f"Событие #{i} | ID: {actual.id[:8]}..."):
                    assert actual.id == expected.id
                    assert actual.created_at == expected.created_at
                    assert actual.created_by == expected.created_by
                    assert actual.title == expected.title
                    assert actual.description == expected.description
                    assert actual.created_by == expected.created_by
                    assert actual.start_date.timestamp() ==  expected.start_date.timestamp()

    @pytest.mark.parametrize(
            'status',
            [
                EventStatusEnum.PUBLISHED,
                EventStatusEnum.CANCELLED,
                EventStatusEnum.FINISHED
            ],
            ids=[
                'PUBLISHED',
                'CANCELLED',
                'FINISHED',
            ]
            )
    @allure.title('Получение списка ивентов с определенным статусом')
    @tag(FeaturesEventMark.GET_EVENTS)
    async def test_get_events_with_filter_status(self, event_service: EventService, event_factory, status, subtests):

        events = await event_factory(count=5, status_event=status)

        filter_obj = EventFilterParams.model_validate({'status': status})

        with allure.step(f'Зпрос списка ивентов со статусом {status}'):
            event_list = await event_service.get_events(filters=filter_obj)

            sorted_actual = sorted(event_list, key=lambda e: e.id)
            sorted_expected = sorted(events, key=lambda e: e.id)

        with allure.step(f'Проверка списка вернувшегося спика ивентов со статусом {status}'):
            assert len(sorted_actual) == len(sorted_expected)

            for event in sorted_actual:
                assert event.status == status

    @allure.title('Получение списка ивентов с пагинацией: skip и limit')
    @tag(FeaturesEventMark.GET_EVENTS)
    async def test_get_events_with_pagination(self, event_service: EventService, event_factory_for_user):

        events = event_factory_for_user

        with allure.step('Запрос первой страницы ивентов (skip=0, limit=5)'):
            page_1 = await event_service.get_events(skip=0, limit=5)

        with allure.step('Запрос второй страницы ивентов (skip=5, limit=5)'):
            page_2 = await event_service.get_events(skip=5, limit=5)

        with allure.step('Проверка пагинации'):
            assert len(page_1) == 5
            assert len(page_2) == 5

        with allure.step('Проверка на дубликаты ивентов на разных страницах'):
            page_ids_1 = {event.id for event in page_1}
            page_ids_2 = {event.id for event in page_2}
            all_ids = page_ids_1 | page_ids_2

            assert page_ids_1.isdisjoint(page_ids_2)
            assert len(all_ids) == 10

    @allure.title('Успешное обновление события создателем')
    @tag(FeaturesEventMark.UPDATE_EVENT)
    async def test_update_event_success(
        self,
        event_service: EventService,
        created_user_with_event,
    ):

        user, event = created_user_with_event

        user_id = user.id
        event_id = event.id


        update_data = EventUpdateModel(
            title="Updated Conference 2026",
            description="Updated description with more details"
        )

        with allure.step('Запрос на обновление события'):
            updated_event = await event_service.update_event(
                event_id=event_id,
                user_id=user_id,
                update_data=update_data
            )

        with allure.step('Проверка обновлённого события'):
            assert updated_event.id == event_id
            assert updated_event.title == "Updated Conference 2026"
            assert updated_event.description == "Updated description with more details"
            assert updated_event.created_by == user_id
            assert updated_event.location == event.location
            assert updated_event.start_date == event.start_date


    @allure.title('Попытка обновления события не создателем (403)')
    @tag(FeaturesEventMark.UPDATE_EVENT)
    async def test_update_event_not_creator(
        self,
        event_service: EventService,
        created_user_with_event,
        organizer_user,
    ):
        _, event = created_user_with_event
        event_id = event.id
        fake_user_id = organizer_user.id

        update_data = EventUpdateModel(title="Hacked Event")

        with allure.step('Попытка обновления события чужим пользователем'):
            with pytest.raises(HTTPException) as err:
                await event_service.update_event(
                    event_id=event_id,
                    user_id=fake_user_id,
                    update_data=update_data
                )

        with allure.step('Проверка что вернулась 403 ошибка'):
            assert err.value.status_code == 403
            assert "not the creator" in err.value.detail.lower()

    @allure.title('Обновление несуществующего события (404)')
    @tag(FeaturesEventMark.UPDATE_EVENT)
    async def test_update_event_not_found(
        self,
        event_service: EventService,
        organizer_user,
    ):

        fake_event_id = event_faker.generate_random_id()
        update_data = EventUpdateModel(title="Fake Event")

        with allure.step('Попытка обновления несуществующего события'):
            with pytest.raises(HTTPException) as err:
                await event_service.update_event(
                    event_id=fake_event_id,
                    user_id=organizer_user.id,
                    update_data=update_data
                )

        with allure.step('Проверка что вернулась 404 ошибка'):
            assert err.value.status_code == 404
            assert "not found" in err.value.detail.lower()


    @allure.title('Смена статуса на CANCELLED устанавливает deleted_at')
    @tag(FeaturesEventMark.UPDATE_EVENT)
    async def test_update_event_status_to_cancelled(
        self,
        event_service: EventService,
        created_user_with_event,
        registration_factory,
    ):

        user, event = created_user_with_event
        event_id = event.id

        with allure.step('Создание регистраций на событие'):
            registrations = await registration_factory(event_id=event_id, count=3)
            assert len(registrations) == 3

        with allure.step('Обновление статуса события на CANCELLED'):
            updated_event = await event_service.update_event(
                event_id=event_id,
                user_id=user.id,
                update_data=EventUpdateModel(status=EventStatusEnum.CANCELLED)
            )

        with allure.step('Проверка что статус обновился'):
            assert updated_event.status == EventStatusEnum.CANCELLED

        with allure.step('Проверка что deleted_at установлен в БД (событие)'):
            raw_event = await event_service.event_dao.get_event(event_id)
            assert raw_event is not None
            assert raw_event.get('deleted_at') is not None
            deleted_at = raw_event['deleted_at']
            if deleted_at.tzinfo is None:
                deleted_at = deleted_at.replace(tzinfo=timezone.utc)

            now = datetime.now(timezone.utc)
            expected_death_time = now + timedelta(seconds=settings.events_config.cleanup_sec)
            time_diff = abs((deleted_at - expected_death_time).total_seconds())
            assert time_diff < 2, f"deleted_at отличается от ожидаемого: {time_diff} сек"

        with allure.step('Проверка что регистрации помечены на удаление'):
            raw_registrations = await event_service.registration_dao.get_event_registrations(event_id)
            for reg in raw_registrations:
                assert reg.get('deleted_at') is not None, "Регистрация не помечена на удаление"


    @allure.title('Частичное обновление события (только title)')
    @tag(FeaturesEventMark.UPDATE_EVENT)
    async def test_update_event_partial_update(
        self,
        event_service: EventService,
        created_user_with_event,
    ):

        user, event = created_user_with_event
        event_id = event.id
        original_description = event.description
        original_location = event.location
        original_start_date = event.start_date
        update_data = EventUpdateModel(title="Only Title Updated")

        with allure.step('Запрос на частичное обновление (только title)'):
            updated_event = await event_service.update_event(
                event_id=event_id,
                user_id=user.id,
                update_data=update_data
            )

        with allure.step('Проверка что обновился только title'):
            assert updated_event.title == "Only Title Updated"
            assert updated_event.description == original_description
            assert updated_event.location == original_location
            assert updated_event.start_date.timestamp() == pytest.approx(
                original_start_date.timestamp(),
                abs=1
            )
            assert updated_event.created_by == user.id

    @allure.title('Успешное удаление события создателем')
    @tag(FeaturesEventMark.DELETE_EVENT)
    async def test_delete_event_success(
        self,
        event_service: EventService,
        created_user_with_event,
    ):

        user, event = created_user_with_event
        event_id = event.id

        with allure.step('Запрос на удаление события создателем'):
            result = await event_service.delete_event(event_id=event_id, user_id=user.id)

        with allure.step('Проверка что возвращается True'):
            assert result is True

        with allure.step('Проверка что событие удалено из БД'):
            deleted_event = await event_service.event_dao.get_event(event_id)
            assert deleted_event is None

    @allure.title('Попытка удаления события не создателем (403)')
    @tag(FeaturesEventMark.DELETE_EVENT)
    async def test_delete_event_not_creator(
        self,
        event_service: EventService,
        created_user_with_event,
        organizer_user,
    ):

        _, event = created_user_with_event
        event_id = event.id
        fake_user_id = organizer_user.id

        with allure.step('Попытка удаления события чужим пользователем'):
            with pytest.raises(HTTPException) as err:
                await event_service.delete_event(event_id=event_id, user_id=fake_user_id)

        with allure.step('Проверка что вернулась 403 ошибка'):
            assert err.value.status_code == 403
            assert "not the creator" in err.value.detail.lower()

    @allure.title('Удаление несуществующего события (404)')
    @tag(FeaturesEventMark.DELETE_EVENT)
    async def test_delete_event_not_found(
        self,
        event_service: EventService,
        organizer_user,
    ):

        fake_event_id = event_faker.generate_random_id()

        with allure.step('Попытка удаления несуществующего события'):
            with pytest.raises(HTTPException) as err:
                await event_service.delete_event(event_id=fake_event_id, user_id=organizer_user.id)

        with allure.step('Проверка что вернулась 404 ошибка'):
            assert err.value.status_code == 404
            assert "not found" in err.value.detail.lower()

    @allure.title('Удаление события удаляет все регистрации (cascade)')
    @tag(FeaturesEventMark.DELETE_EVENT)
    async def test_delete_event_cascade_registrations(
        self,
        event_service: EventService,
        created_user_with_event,
        registration_factory,
    ):

        user, event = created_user_with_event
        event_id = event.id

        with allure.step('Создание 5 регистраций на событие'):
            registrations = await registration_factory(event_id=event_id, count=5)
            assert len(registrations) == 5

        with allure.step('Проверка что регистрации существуют в БД'):
            event_regs_before = await event_service.registration_dao.get_event_registrations(event_id)
            assert len(event_regs_before) == 5

        with allure.step('Запрос на удаление события'):
            result = await event_service.delete_event(event_id=event_id, user_id=user.id)

        with allure.step('Проверка что событие удалено'):
            assert result is True
            deleted_event = await event_service.event_dao.get_event(event_id)
            assert deleted_event is None

        with allure.step('Проверка что все регистрации удалены (cascade)'):
            event_regs_after = await event_service.registration_dao.get_event_registrations(event_id)
            assert len(event_regs_after) == 0

    @allure.title('Удаление события администратором (без проверки created_by)')
    @tag(FeaturesEventMark.DELETE_EVENT)
    async def test_delete_event_for_admin_success(
        self,
        event_service: EventService,
        created_user_with_event,
    ):

        _, event = created_user_with_event
        event_id = event.id

        with allure.step('Запрос на удаление события администратором'):
            result = await event_service.delete_event_for_admin(event_id=event_id)

        with allure.step('Проверка что возвращается True'):
            assert result is True

        with allure.step('Проверка что событие удалено из БД'):
            deleted_event = await event_service.event_dao.get_event(event_id)
            assert deleted_event is None

    @allure.title('Удаление несуществующего события администратором (404)')
    @tag(FeaturesEventMark.DELETE_EVENT)
    async def test_delete_event_for_admin_not_found(
        self,
        event_service: EventService,
    ):

        fake_event_id = event_faker.generate_random_id()

        with allure.step('Попытка удаления несуществующего события администратором'):
            with pytest.raises(HTTPException) as err:
                await event_service.delete_event_for_admin(event_id=fake_event_id)

        with allure.step('Проверка что вернулась 404 ошибка'):
            assert err.value.status_code == 404
            assert "not found" in err.value.detail.lower()

    @allure.title('Успешная регистрация на событие')
    @tag(FeaturesEventMark.EVENT_REGISTRATION)
    async def test_register_for_event_success(
        self,
        event_service: EventService,
        created_user_with_event,
    ):
        user, event = created_user_with_event
        event_id = event.id
        user_id = user.id

        with allure.step('Запрос на регистрацию пользователя на событие'):
            result = await event_service.register_for_event(event_id=event_id, user_id=user_id)

        with allure.step('Проверка что возвращается статус registered'):
            assert result == {"status": "registered", "event_id": event_id}

        with allure.step('Проверка что регистрация создана в БД'):
            registration = await event_service.registration_dao.get_existing_registration(event_id, user_id)
            assert registration is not None
            assert str(registration["event_id"]) == event_id
            assert str(registration["user_id"]) == user_id

    @allure.title('Повторная регистрация на событие (400)')
    @tag(FeaturesEventMark.EVENT_REGISTRATION)
    async def test_register_for_event_duplicate(
        self,
        event_service: EventService,
        created_user_with_event,
        registration_factory,
    ):
        user, event = created_user_with_event
        event_id = event.id
        user_id = user.id

        with allure.step('Создание первой регистрации'):
            await registration_factory(event_id=event_id, user_id=user_id, count=1)

        with allure.step('Попытка повторной регистрации'):
            with pytest.raises(HTTPException) as err:
                await event_service.register_for_event(event_id=event_id, user_id=user_id)

        with allure.step('Проверка что вернулась 400 ошибка'):
            assert err.value.status_code == 400
            assert "already registered" in err.value.detail.lower()

    @allure.title('Регистрация на заполненное событие (400)')
    @tag(FeaturesEventMark.EVENT_REGISTRATION)
    @pytest.mark.xfail(reason="mongomock не поддерживает .limit() корректно для асинхронных курсоров")
    async def test_register_for_event_full(
        self,
        event_service: EventService,
        created_user_with_limited_event,
        registration_factory,
        user_factory,
    ):
        _, event = created_user_with_limited_event
        event_id = event.id
        max_participants = event.max_participants

        with allure.step(f'Заполнение события на {max_participants - 1} участников'):
            await registration_factory(event_id=event_id, count=max_participants - 1)

        with allure.step('Попытка регистрации — должна пройти (ещё есть места)'):
            new_user_id = await user_factory()
            result = await event_service.register_for_event(event_id=event_id, user_id=new_user_id)
            assert result["status"] == "registered"

        with allure.step('Попытка регистрации следующего пользователя — должна вызвать ошибку (мест нет)'):
            another_user_id = await user_factory()
            with pytest.raises(HTTPException) as err:
                await event_service.register_for_event(event_id=event_id, user_id=another_user_id)

        with allure.step('Проверка что вернулась 400 ошибка'):
            assert err.value.status_code == 400
            assert "full" in err.value.detail.lower()

    @allure.title('Регистрация на несуществующее событие (404)')
    @tag(FeaturesEventMark.EVENT_REGISTRATION)
    async def test_register_for_event_not_found(
        self,
        event_service: EventService,
        created_user,
    ):
        user, *_ = created_user
        user_id = user.id
        fake_event_id = event_faker.generate_random_id()

        with allure.step('Попытка регистрации на несуществующее событие'):
            with pytest.raises(HTTPException) as err:
                await event_service.register_for_event(event_id=fake_event_id, user_id=user_id)

        with allure.step('Проверка что вернулась 404 ошибка'):
            assert err.value.status_code == 404
            assert "not found" in err.value.detail.lower()

    @allure.title('Регистрация с невалидным ID события (400)')
    @tag(FeaturesEventMark.EVENT_REGISTRATION)
    async def test_register_for_event_invalid_id(
        self,
        event_service: EventService,
        created_user,
    ):
        user, *_ = created_user
        user_id = user.id
        invalid_event_id = "invalid-object-id"

        with allure.step('Попытка регистрации с невалидным ID события'):
            with pytest.raises(HTTPException) as err:
                await event_service.register_for_event(event_id=invalid_event_id, user_id=user_id)

        with allure.step('Проверка что вернулась 400 ошибка'):
            assert err.value.status_code == 400
            assert "invalid" in err.value.detail.lower()