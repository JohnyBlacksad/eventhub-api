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

