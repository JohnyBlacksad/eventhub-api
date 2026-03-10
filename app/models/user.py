from bson import ObjectId
from app.database import db_client

class UserDAO:
    def __init__(self):
        self.collection = db_client.get_db()['users'] # pyright: ignore[reportOptionalSubscript]

    @classmethod
    async def setup_indexes(cls):
        instance = cls()
        await instance.collection.create_index('email', unique=True)

    async def create_user(self, user_data: dict) -> str:
        result = await self.collection.insert_one(user_data)
        return str(result.inserted_id)

    async def get_user_by_id(self, user_id: str):
        query_filter = {'_id': ObjectId(user_id)}
        result = await self.collection.find_one(query_filter)
        return result

    async def get_user_by_email(self, email: str):
        query_filter = {'email': email}
        result = await self.collection.find_one(query_filter)
        return result

    async def update_user(self, user_id: str, update_data: dict):
        query_filter = {'_id': ObjectId(user_id)}
        result = await self.collection.update_one(query_filter, {'$set': update_data})
        return await self.get_user_by_id(user_id)

    async def delete_user(self, user_id: str):
        query_filter = {'_id': ObjectId(user_id)}
        result = await self.collection.delete_one(query_filter)
        return result.deleted_count > 0