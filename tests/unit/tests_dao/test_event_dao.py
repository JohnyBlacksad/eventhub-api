from datetime import datetime, timedelta, timezone

from mongomock import ObjectId
from mongomock_motor import AsyncMongoMockCollection
import pytest
from app.models.events import EventDAO
from tests.core.const.mark_enums import (
    tag,
    MarkTests,
    ModuleMarks,
    ServicesMark,
    DataBaseFunctionMark
)

@tag(MarkTests.UNITS)
@tag(ModuleMarks.DAO)
@tag(ServicesMark.EVENTS)
@pytest.mark.asyncio
class TestEventDAO:

    @tag(DataBaseFunctionMark.SETUP_INDEXES)
    async def test_setup_indexes_create_all_indexes(self, event_collection: AsyncMongoMockCollection, subtests):
        await EventDAO.setup_indexes(event_collection)

        indexes = await event_collection.index_information()

        with subtests.test(msg='asserts indexes'):
            assert len(indexes) == 5
            assert '_id_' in indexes
            assert 'startDate_1' in indexes
            assert 'title_text' in indexes
            assert 'location.city_1_status_1' in indexes
            assert 'deleted_at_1' in indexes


    @pytest.mark.setup_indexes
    @pytest.mark.asyncio
    async def test_setup_indexes_startDate_is_ascending(self, event_collection: AsyncMongoMockCollection):
        """Проверка что индекс startDate — ASCENDING."""
        await EventDAO.setup_indexes(event_collection)

        indexes = await event_collection.index_information()

        assert indexes['startDate_1']['key'] == [('startDate', 1)]


    @pytest.mark.setup_indexes
    @pytest.mark.asyncio
    async def test_setup_indexes_title_is_text(self, event_collection: AsyncMongoMockCollection):
        """Проверка что индекс title — TEXT."""
        await EventDAO.setup_indexes(event_collection)

        indexes = await event_collection.index_information()

        assert indexes['title_text']['key'] == [('_fts', 'text'), ('_ftsx', 1)]


    @pytest.mark.setup_indexes
    @pytest.mark.asyncio
    async def test_setup_indexes_location_city_status_is_compound(self, event_collection: AsyncMongoMockCollection):
        """Проверка что индекс location.city + status — составной."""
        await EventDAO.setup_indexes(event_collection)

        indexes = await event_collection.index_information()

        compound_index = indexes['location.city_1_status_1']['key']
        assert ('location.city', 1) in compound_index
        assert ('status', 1) in compound_index


    @pytest.mark.setup_indexes
    @pytest.mark.asyncio
    async def test_setup_indexes_deleted_at_is_ttl(self, event_collection: AsyncMongoMockCollection):
        """Проверка что индекс deleted_at — TTL."""
        await EventDAO.setup_indexes(event_collection)

        indexes = await event_collection.index_information()

        ttl_index = indexes['deleted_at_1']
        assert ttl_index['expireAfterSeconds'] == 0


    @pytest.mark.create_event
    @pytest.mark.asyncio
    async def test_create_event_returns_id(self, event_dao: EventDAO):
        """Создание события возвращает ID."""
        event_data = {
            'title': 'Test Event',
            'description': 'Test Description',
            'startDate': datetime.now(timezone.utc),
            'endDate': datetime.now(timezone.utc) + timedelta(hours=1),
            'location': {'city': 'Moscow', 'country': 'Russia'},
            'status': 'published',
            'created_by': str(ObjectId())
        }

        event_id = await event_dao.create_event(event_data)

        assert isinstance(event_id, str)

        db_event = await event_dao.get_event(event_id)
        assert db_event is not None
        assert db_event['title'] == event_data['title']


    @pytest.mark.get_event
    @pytest.mark.asyncio
    async def test_get_event_returns_event(self, event_dao: EventDAO, created_event: dict):
        """Получение события по ID возвращает событие."""
        event_id = created_event['_id']

        event = await event_dao.get_event(event_id)

        assert event is not None
        assert event['_id'] == event_id
        assert event['title'] == created_event['title']


    @pytest.mark.get_event
    @pytest.mark.asyncio
    async def test_get_event_returns_none_if_not_found(self, event_dao: EventDAO):
        """Получение несуществующего события возвращает None."""
        fake_id = str(ObjectId())

        event = await event_dao.get_event(fake_id)

        assert event is None


    @pytest.mark.update_event
    @pytest.mark.asyncio
    async def test_update_event_updates_fields(self, event_dao: EventDAO, created_event: dict):
        """Обновление события обновляет поля."""
        event_id = created_event['_id']
        update_data = {'title': 'Updated Title'}

        updated = await event_dao.update_event(event_id, update_data)

        assert updated is not None
        assert updated['title'] == 'Updated Title'


    @pytest.mark.update_event
    @pytest.mark.asyncio
    async def test_update_event_returns_none_if_not_found(self, event_dao: EventDAO):
        """Обновление несуществующего события возвращает None."""
        fake_id = str(ObjectId())

        updated = await event_dao.update_event(fake_id, {'title': 'Test'})

        assert updated is None


    @pytest.mark.delete_event
    @pytest.mark.asyncio
    async def test_delete_event_returns_true(self, event_dao: EventDAO, created_event: dict):
        """Удаление события возвращает True."""
        event_id = created_event['_id']

        result = await event_dao.delete_event(event_id)

        assert result is True

        deleted = await event_dao.get_event(event_id)
        assert deleted is None


    @pytest.mark.delete_event
    @pytest.mark.asyncio
    async def test_delete_event_returns_false_if_not_found(self, event_dao: EventDAO):
        """Удаление несуществующего события возвращает False."""
        fake_id = str(ObjectId())

        result = await event_dao.delete_event(fake_id)

        assert result is False


    @pytest.mark.has_active_events
    @pytest.mark.asyncio
    async def test_has_active_events_returns_true(self, event_dao: EventDAO, created_event: dict):
        """Проверка активных событий возвращает True если есть published."""
        user_id = created_event['created_by']

        has_active = await event_dao.has_active_events(user_id)

        assert has_active is True


    @pytest.mark.has_active_events
    @pytest.mark.asyncio
    async def test_has_active_events_returns_false(self, event_dao: EventDAO):
        """Проверка активных событий возвращает False если нет событий."""
        fake_id = str(ObjectId())

        has_active = await event_dao.has_active_events(fake_id)

        assert has_active is False


    @pytest.mark.delete_events_by_user
    @pytest.mark.asyncio
    async def test_delete_events_by_user_returns_true(self, event_dao: EventDAO, created_event: dict):
        """Удаление всех событий пользователя возвращает True."""
        user_id = created_event['created_by']

        result = await event_dao.delete_events_by_user(user_id)

        assert result is True


    @pytest.mark.get_events
    @pytest.mark.asyncio
    async def test_get_events_returns_list(self, event_dao: EventDAO):
        """Получение списка событий возвращает список."""
        events = await event_dao.get_events()

        assert isinstance(events, list)


    @pytest.mark.get_events
    @pytest.mark.asyncio
    async def test_get_events_with_filter_status(self, event_dao: EventDAO, created_event: dict):
        """Фильтр по статусу работает."""
        from app.schemas.event import EventFilterParams

        filter_obj = EventFilterParams(status=created_event['status'])  # type: ignore

        events = await event_dao.get_events(filter_obj=filter_obj)

        assert len(events) >= 1
        assert events[0]['status'] == created_event['status']