from bson import ObjectId
from app.database import db_client
from motor.motor_asyncio import AsyncIOMotorCollection
from pymongo import ReturnDocument, ASCENDING, TEXT

class EventDAO:
    def __init__(self, collections: AsyncIOMotorCollection):
        self.collections = collections

    @classmethod
    async def setup_indexes(cls, collection: AsyncIOMotorCollection):
        await collection.create_index([("startDate", ASCENDING)])
        await collection.create_index([('title', TEXT)])
        await collection.create_index([('locations.city', ASCENDING),
                                       ('status', ASCENDING)])

    async def create_event(self, event_data: dict) -> str:
        result = await self.collections.insert_one(event_data)
        return str(result.inserted_id)

    async def get_event(self, event_id: str) -> dict | None:
        payload = {'_id': ObjectId(event_id)}
        result = await self.collections.find_one(payload)
        return result

    async def get_events(
            self,
            filter: dict = None,  # type: ignore
            skip: int = 0,
            limit: int = 10
    ) -> list[dict]:
        cursor = (self.collections
                  .find(filter or {})
                  .sort('startDate', ASCENDING)
                  .skip(skip)
                  .limit(limit)
                )

        return await cursor.to_list(length=limit)


    async def update_event(self, event_id: str, event_data: dict):
        payload = {'_id': ObjectId(event_id)}
        updated_event = await self.collections.find_one_and_update(
            payload,
            {'$set': event_data},
            return_document=ReturnDocument.AFTER
        )
        return updated_event

    async def delete_event(self, event_id: str):
        payload = {'_id': ObjectId(event_id)}
        result = await self.collections.delete_one(payload)
        return result.deleted_count > 0