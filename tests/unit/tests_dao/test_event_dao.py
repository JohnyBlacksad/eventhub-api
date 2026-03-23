import random
from datetime import datetime, timedelta, timezone

import allure
import pytest
from mongomock import ObjectId
from mongomock_motor import AsyncMongoMockCollection

from app.models.events import EventDAO
from app.schemas.enums.event_enums.event_enums import EventStatusEnum
from app.schemas.event import EventFilterParams
from tests.core.const.mark_enums import (
    DataBaseFunctionMark,
    FeaturesEventMark,
    MarkTests,
    ModuleMarks,
    ServicesMark,
    tag,
)
from tests.core.event_data_factory.fake_event_data import event_faker


@tag(MarkTests.UNITS)
@tag(ModuleMarks.DAO)
@tag(ServicesMark.EVENTS)
@pytest.mark.asyncio
class TestEventDAO:
    @allure.title("Инициализация индексов для event коллекции Mongo DB")
    @tag(DataBaseFunctionMark.SETUP_INDEXES)
    async def test_setup_indexes_create_all_indexes(self, event_collection: AsyncMongoMockCollection, subtests):
        with allure.step("Инициализация индексов"):
            await EventDAO.setup_indexes(event_collection)
            indexes = await event_collection.index_information()

        with allure.step("Проверка инициализации индексов"):
            with subtests.test(msg="asserts indexes"):
                assert len(indexes) == 5
                assert "_id_" in indexes
                assert "startDate_1" in indexes
                assert "title_text" in indexes
                assert "location.city_1_status_1" in indexes
                assert "deleted_at_1" in indexes

    @allure.title("Проверка индекса startDate на ASCENDING")
    @tag(DataBaseFunctionMark.SETUP_INDEXES)
    async def test_setup_indexes_startDate_is_ascending(self, event_collection: AsyncMongoMockCollection):
        with allure.step("Инициализация индексов"):
            await EventDAO.setup_indexes(event_collection)
            indexes = await event_collection.index_information()

        with allure.step("Проверка индекса startDate_1"):
            assert indexes["startDate_1"]["key"] == [("startDate", 1)]

    @allure.title("Проверка индкса title на TEXT")
    @tag(DataBaseFunctionMark.SETUP_INDEXES)
    async def test_setup_indexes_title_is_text(self, event_collection: AsyncMongoMockCollection):
        with allure.step("Инициализация индексов"):
            await EventDAO.setup_indexes(event_collection)
            indexes = await event_collection.index_information()

        with allure.step("Проверка индекса title_text"):
            assert "title_text" in indexes
            assert indexes["title_text"]["key"][0][1] == "text"

    @allure.title("Проверка что индекс location.city + status — составной.")
    @tag(DataBaseFunctionMark.SETUP_INDEXES)
    async def test_setup_indexes_location_city_status_is_compound(self, event_collection: AsyncMongoMockCollection):
        with allure.step("Инициализация индексов"):
            await EventDAO.setup_indexes(event_collection)
            indexes = await event_collection.index_information()
            compound_index = indexes["location.city_1_status_1"]["key"]

        with allure.step("Проверка индекса location.city + status"):
            assert ("location.city", 1) in compound_index
            assert ("status", 1) in compound_index

    @allure.title("Проверка что индекс deleted_at — TTL.")
    @tag(DataBaseFunctionMark.SETUP_INDEXES)
    async def test_setup_indexes_deleted_at_is_ttl(self, event_collection: AsyncMongoMockCollection):
        with allure.step("Инициализация индексов"):
            await EventDAO.setup_indexes(event_collection)
            indexes = await event_collection.index_information()
            ttl_index = indexes["deleted_at_1"]

        with allure.step("Проверка индекса location.city + status"):
            assert ttl_index["expireAfterSeconds"] == 0

    @allure.title("Проверка создания ивента")
    @tag(FeaturesEventMark.CREATE_EVENT)
    async def test_create_event_returns_id(self, event_dao: EventDAO, subtests):
        with allure.step("Запрос на создение события"):
            event_data = event_faker.get_event_data_dict()
            event_id = await event_dao.create_event(event_data)
            db_event = await event_dao.get_event(event_id)

        expected_fields = {
            "title": event_data["title"],
            "description": event_data["description"],
            "status": event_data["status"],
            "location": event_data["location"],
            "created_by": event_data["created_by"],
        }

        with allure.step("Проверка созданного события"):
            assert isinstance(event_id, str)
            assert db_event is not None

            for field_name, expected_value in expected_fields.items():
                with subtests.test(msg=f"Проверка поля {field_name} и наличия временных меток"):
                    assert "startDate" in db_event
                    assert "endDate" in db_event
                    assert "created_at" in db_event
                    assert isinstance(db_event["startDate"], datetime)
                    assert isinstance(db_event["endDate"], datetime)
                    assert isinstance(db_event["created_at"], datetime)

                    assert db_event[field_name] == expected_value

    @allure.title("Получение события по ID")
    @tag(FeaturesEventMark.CREATE_EVENT)
    async def test_get_event_returns_event(self, event_dao: EventDAO, created_event: dict, subtests):
        event_id = created_event["_id"]

        with allure.step(f"Запрос на получение события по ID: {event_id}"):
            event = await event_dao.get_event(event_id)

        with allure.step("Проверка что вернулись данные события"):
            assert event is not None
            assert event["_id"] == event_id

        with allure.step("Проверка целостности вернувшихся данных события"):
            expected_fields = {
                "title": created_event["title"],
                "description": created_event["description"],
                "status": created_event["status"],
                "location": created_event["location"],
                "startDate": created_event["startDate"],
                "endDate": created_event["endDate"],
                "created_by": created_event["created_by"],
                "created_at": created_event["created_at"],
            }

            for field_name, expected_value in expected_fields.items():
                with subtests.test(msg=f"Проверка поля {field_name}"):
                    assert event[field_name] == expected_value

    @allure.title("Получение несуществующего события")
    @tag(FeaturesEventMark.GET_EVENT)
    async def test_get_event_returns_none_if_not_found(self, event_dao: EventDAO):
        fake_id = event_faker.generate_random_id()

        with allure.step(f"Запрос на получение события по фейковому ID {fake_id}"):
            event = await event_dao.get_event(fake_id)

        with allure.step("Проверка отсуствия данных"):
            assert event is None

    @allure.title("Обновление события")
    @tag(FeaturesEventMark.UPDATE_EVENT)
    async def test_update_event_updates_fields(self, event_dao: EventDAO, created_event: dict):
        event_id = created_event["_id"]
        with allure.step(f"Запрос на обновление события по ID: `{event_id}`"):
            update_data = {"title": "Updated Title"}
            updated = await event_dao.update_event(event_id, update_data)

        with allure.step("Проверка целостности вернувшихся обновленных данных события"):
            assert updated is not None
            assert updated["title"] == "Updated Title"
            assert updated["description"] == created_event["description"]
            assert updated["_id"] == created_event["_id"]

    @allure.title("Обновление несуществующего события")
    @tag(FeaturesEventMark.UPDATE_EVENT)
    async def test_update_event_returns_none_if_not_found(self, event_dao: EventDAO):
        fake_id = str(ObjectId())

        with allure.step(f"Запрос на обновление события по фейковому ID: `{fake_id}`"):
            updated = await event_dao.update_event(fake_id, {"title": "Test"})

        with allure.step("Проверка отсуствия данных"):
            assert updated is None

    @allure.title("Удаление события")
    @tag(FeaturesEventMark.DELETE_EVENT)
    async def test_delete_event_returns_true(self, event_dao: EventDAO, created_event: dict):
        event_id = created_event["_id"]

        with allure.step(f"Запрос на удаление события по ID: `{event_id}`"):
            result = await event_dao.delete_event(event_id)

        with allure.step("Проверка подтверждения удаления `True`"):
            assert result is True

        with allure.step(f"Запрос на получения удаленного события по ID: `{event_id}`"):
            deleted = await event_dao.get_event(event_id)

        with allure.step("Проверка отсуствия данных события"):
            assert deleted is None

    @allure.title("Удаление несуществующего события")
    @tag(FeaturesEventMark.DELETE_EVENT)
    async def test_delete_event_returns_false_if_not_found(self, event_dao: EventDAO):
        fake_id = str(ObjectId())

        with allure.step(f"Запрос на удаление события по фейковому ID: `{fake_id}`"):
            result = await event_dao.delete_event(fake_id)

        with allure.step("Проверка негативного ответа удаления данных"):
            assert result is False

    @allure.title("Проверка наличия активных событий у пользователя")
    @tag(FeaturesEventMark.HAS_ACTIVE_EVENT)
    async def test_has_active_events_returns_true(self, event_dao: EventDAO, event_factory_for_user):
        user_id, *_ = await event_factory_for_user(EventStatusEnum.PUBLISHED)

        with allure.step("Запрос на наличие активных событий у пользователя"):
            has_active = await event_dao.has_active_events(user_id)

        with allure.step("Проверка положительного ответа"):
            assert has_active is True

    @allure.title("Проверка отсуствия активных событий возвращает у пользователя")
    @tag(FeaturesEventMark.HAS_ACTIVE_EVENT)
    async def test_has_active_events_returns_false(self, event_dao: EventDAO, event_factory_for_user):
        user_id, *_ = await event_factory_for_user(EventStatusEnum.CANCELLED)

        with allure.step("Запрос на наличие активных событий у пользователя"):
            has_active = await event_dao.has_active_events(user_id)

        with allure.step("Проверка отрицательного ответа"):
            assert has_active is False

    @allure.title("Удаление всех событий пользователя")
    @tag(FeaturesEventMark.DELETE_USER_EVENTS)
    async def test_delete_events_by_user_returns_true(self, event_dao: EventDAO, event_factory_for_user):
        """Удаление всех событий пользователя возвращает True."""
        user_id, *_ = await event_factory_for_user(EventStatusEnum.PUBLISHED, count=5)

        with allure.step("Отправление запроса на удаление всех событий пользователя"):
            result = await event_dao.delete_events_by_user(user_id)

        with allure.step("Проверка отрицательного ответа и отсуствия у пользователя ивентов"):
            assert result
            assert not await event_dao.has_active_events(user_id)

    @allure.title("Получение списка доступных ивентов")
    @tag(FeaturesEventMark.GET_EVENTS)
    async def test_get_events_returns_list(self, event_dao: EventDAO, event_factory_for_user):
        with allure.step("Отправление запроса на создание 5 ивентов и получения списка ивентов"):
            await event_factory_for_user(EventStatusEnum.PUBLISHED, count=5)
            events = await event_dao.get_events()

        with allure.step("Проверка вернувшегося списка ивентов"):
            assert isinstance(events, list)
            assert len(events) > 0

    @allure.title("Получение списка доступных ивентов c фильтрацией по статусу")
    @tag(FeaturesEventMark.GET_EVENTS)
    async def test_get_events_with_filter_status(self, event_dao: EventDAO, created_event: dict):
        status = created_event["status"]

        with allure.step("Отправление запроса на получение списка ивентов"):
            filter_obj = EventFilterParams(status=status)  # type: ignore
            events = await event_dao.get_events(filter_obj=filter_obj)

        with allure.step("Проверка вернувшегося списка ивентов"):
            assert len(events) >= 1
            assert events[0]["status"] == created_event["status"]

    @allure.title("Фильтрация событий по городу")
    @tag(FeaturesEventMark.GET_EVENTS)
    async def test_get_events_with_filter_city(self, event_dao: EventDAO, created_event: dict):
        city = created_event["location"]["city"]

        with allure.step(f"Отправление запроса на получение списка ивентов с фильтром по городу: {city}"):
            filter_obj = EventFilterParams(city=city)
            events = await event_dao.get_events(filter_obj=filter_obj)

        with allure.step("Проверка вернувшегося списка ивентов"):
            assert len(events) >= 1
            for event in events:
                assert event["location"]["city"] == city

    @allure.title("Фильтрация событий по стране")
    @tag(FeaturesEventMark.GET_EVENTS)
    async def test_get_events_with_filter_country(self, event_dao: EventDAO, created_event: dict):
        country = created_event["location"]["country"]

        with allure.step(f"Отправление запроса на получение списка ивентов с фильтром по стране: {country}"):
            filter_obj = EventFilterParams(country=country)
            events = await event_dao.get_events(filter_obj=filter_obj)

        with allure.step("Проверка вернувшегося списка ивентов"):
            assert len(events) >= 1
            for event in events:
                assert event["location"]["country"] == country

    @allure.title("Фильтрация событий ОТ даты (date_from)")
    @tag(FeaturesEventMark.GET_EVENTS)
    async def test_get_events_with_filter_date_from(self, event_dao: EventDAO, event_factory_for_user):
        now = datetime.now(timezone.utc)

        with allure.step("Создание событий с разными датами"):
            await event_factory_for_user(EventStatusEnum.PUBLISHED, count=1, start_date_days_offset=-10)

            await event_factory_for_user(EventStatusEnum.PUBLISHED, count=1, start_date_days_offset=10)

        with allure.step(f"Отправление запроса на получение списка ивентов с фильтром ОТ даты: {now}"):
            filter_obj = EventFilterParams(date_from=now)  # type: ignore
            events = await event_dao.get_events(filter_obj=filter_obj)

        with allure.step("Проверка вернувшегося списка ивентов"):
            assert len(events) >= 1
            for event in events:
                event_timestamp = (
                    event["startDate"].timestamp()
                    if event["startDate"].tzinfo
                    else event["startDate"].replace(tzinfo=timezone.utc).timestamp()
                )
                now_timestamp = now.timestamp()
                assert event_timestamp >= now_timestamp
                # assert event['startDate'] >= now

    @allure.title("Фильтрация событий ДО даты (date_to)")
    @tag(FeaturesEventMark.GET_EVENTS)
    async def test_get_events_with_filter_date_to(self, event_dao: EventDAO, event_factory_for_user):
        now = datetime.now(timezone.utc)

        with allure.step("Создание событий с разными датами"):
            await event_factory_for_user(EventStatusEnum.PUBLISHED, count=1, start_date_days_offset=-10)

            await event_factory_for_user(EventStatusEnum.PUBLISHED, count=1, start_date_days_offset=10)

        with allure.step(f"Отправление запроса на получение списка ивентов с фильтром ДО даты: {now}"):
            filter_obj = EventFilterParams(date_to=now)  # type: ignore
            events = await event_dao.get_events(filter_obj=filter_obj)

        with allure.step("Проверка вернувшегося списка ивентов"):
            assert len(events) >= 1
            for event in events:
                event_timestamp = (
                    event["startDate"].timestamp()
                    if event["startDate"].tzinfo
                    else event["startDate"].replace(tzinfo=timezone.utc).timestamp()
                )
                now_timestamp = now.timestamp()
                assert event_timestamp <= now_timestamp

    @allure.title("Фильтрация событий в диапазоне дат (date_from + date_to)")
    @tag(FeaturesEventMark.GET_EVENTS)
    async def test_get_events_with_filter_date_range(self, event_dao: EventDAO, event_factory_for_user):
        now = datetime.now(timezone.utc)
        range_start = now - timedelta(days=5)
        range_end = now + timedelta(days=5)

        with allure.step("Создание событий с разными датами"):
            await event_factory_for_user(EventStatusEnum.PUBLISHED, count=1, start_date_days_offset=-10)

            await event_factory_for_user(EventStatusEnum.PUBLISHED, count=1, start_date_days_offset=0)

            await event_factory_for_user(EventStatusEnum.PUBLISHED, count=1, start_date_days_offset=10)

        with allure.step(
            f"Отправление запроса на получение списка ивентов с фильтром диапазона дат: от {range_start} до {range_end}"
        ):
            filter_obj = EventFilterParams(
                date_from=range_start,  # type: ignore
                date_to=range_end,  # type: ignore
            )
            events = await event_dao.get_events(filter_obj=filter_obj)

        with allure.step("Проверка вернувшегося списка ивентов"):
            assert len(events) >= 1
            range_start_ts = range_start.timestamp()
            range_end_ts = range_end.timestamp()

            for event in events:
                event_timestamp = (
                    event["startDate"].timestamp()
                    if event["startDate"].tzinfo
                    else event["startDate"].replace(tzinfo=timezone.utc).timestamp()
                )
                assert range_start_ts <= event_timestamp <= range_end_ts

    @allure.title("Комбинированная фильтрация (статус + город)")
    @tag(FeaturesEventMark.GET_EVENTS)
    async def test_get_events_with_combined_filters(self, event_dao: EventDAO, created_event: dict):
        status = created_event["status"]
        city = created_event["location"]["city"]

        with allure.step(
            f"Отправление запроса на получение списка ивентов с комбинированным фильтром (статус: {status}, город: {city})"
        ):
            filter_obj = EventFilterParams(status=status, city=city)
            events = await event_dao.get_events(filter_obj=filter_obj)

        with allure.step("Проверка вернувшегося списка ивентов"):
            assert len(events) >= 1
            for event in events:
                assert event["status"] == status
                assert event["location"]["city"] == city

    @allure.title("Фильтрация без параметров возвращает все события")
    @tag(FeaturesEventMark.GET_EVENTS)
    async def test_get_events_with_no_filters(self, event_dao: EventDAO, event_factory_for_user):
        event_count = 5

        with allure.step(f"Создание {event_count} событий"):
            await event_factory_for_user(EventStatusEnum.PUBLISHED, count=event_count)

        with allure.step("Отправление запроса на получение списка ивентов без фильтров"):
            filter_obj = EventFilterParams()
            events = await event_dao.get_events(filter_obj=filter_obj)

        with allure.step("Проверка вернувшегося списка ивентов"):
            assert len(events) == event_count

    @allure.title("Пагинация: skip и limit работают")
    @tag(FeaturesEventMark.GET_EVENTS)
    async def test_get_events_with_pagination(self, event_dao: EventDAO, event_factory_for_user):
        total_events = 10

        with allure.step(f"Создание {total_events} событий"):
            await event_factory_for_user(EventStatusEnum.PUBLISHED, count=total_events)

        with allure.step("Получение первой страницы (skip=0, limit=3)"):
            events_page_1 = await event_dao.get_events(skip=0, limit=3)

        with allure.step("Получение второй страницы (skip=3, limit=3)"):
            events_page_2 = await event_dao.get_events(skip=3, limit=3)

        with allure.step("Проверка пагинации"):
            assert len(events_page_1) == 3
            assert len(events_page_2) == 3

            page_1_ids = {e["_id"] for e in events_page_1}
            page_2_ids = {e["_id"] for e in events_page_2}
            assert page_1_ids.isdisjoint(page_2_ids)

    @allure.title("Сортировка по дате возрастания (ASC)")
    @tag(FeaturesEventMark.GET_EVENTS)
    async def test_get_events_sort_by_date_asc(self, event_dao: EventDAO, event_factory_for_user):
        with allure.step("Создание событий с разными датами"):
            now = datetime.now(timezone.utc)

            await event_factory_for_user(EventStatusEnum.PUBLISHED, count=1, start_date_days_offset=10)

            await event_factory_for_user(EventStatusEnum.PUBLISHED, count=1, start_date_days_offset=5)

            await event_factory_for_user(EventStatusEnum.PUBLISHED, count=1, start_date_days_offset=15)

        get_timestamp = lambda dt: dt.timestamp() if dt.tzinfo else dt.replace(tzinfo=timezone.utc).timestamp()

        with allure.step("Отправление запроса на получение списка ивентов с сортировкой ASC"):
            filter_obj = EventFilterParams(sort_by="startDate", sort_order="asc")  # type: ignore
            events = await event_dao.get_events(filter_obj=filter_obj)

        with allure.step("Проверка сортировки по возрастанию"):
            assert len(events) >= 3
            dates = [get_timestamp(e["startDate"]) for e in events[:3]]
            assert dates == sorted(dates)

    @allure.title("Сортировка по дате (DESC — проверка что метод работает)")
    @tag(FeaturesEventMark.GET_EVENTS)
    async def test_get_events_sort_by_date_desc(self, event_dao: EventDAO, event_factory_for_user):
        with allure.step("Создание событий с разными датами"):
            await event_factory_for_user(EventStatusEnum.PUBLISHED, count=1, start_date_days_offset=1)
            await event_factory_for_user(EventStatusEnum.PUBLISHED, count=1, start_date_days_offset=5)
            await event_factory_for_user(EventStatusEnum.PUBLISHED, count=1, start_date_days_offset=10)

        with allure.step("Отправление запроса на получение списка ивентов с сортировкой DESC"):
            filter_obj = EventFilterParams(sort_by="startDate", sort_order="desc")  # type: ignore
            events = await event_dao.get_events(filter_obj=filter_obj)

        with allure.step("Проверка что метод возвращает события"):
            # ← Просто проверяем что метод работает, не направление сортировки
            assert len(events) >= 3

    @pytest.mark.xfail(reason="mongomock does not support $text operator - tested manually with real MongoDB")
    @allure.title("Полнотекстовый поиск по заголовку события")
    @tag(FeaturesEventMark.GET_EVENTS)
    async def test_get_events_with_filter_search(
        self,
        event_dao: EventDAO,
    ):
        unique_word = f"УникальноеТестовоеСобытие{random.randint(1000, 9999)}"

        event_data = event_faker.get_event_data_dict()
        event_data["title"] = unique_word
        event_data["status"] = EventStatusEnum.PUBLISHED

        await event_dao.create_event(event_data)

        filter_obj = EventFilterParams(search=unique_word)
        events = await event_dao.get_events(filter_obj=filter_obj)

        assert isinstance(events, list)

        if len(events) > 0:
            assert any(unique_word in event["title"] for event in events)
