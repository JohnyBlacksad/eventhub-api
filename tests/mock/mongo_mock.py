from mongomock_motor import AsyncMongoMockClient
from mongomock_motor import AsyncMongoMockCollection

class MockEventDatabase:

    def __init__(self):
        self.client = AsyncMongoMockClient()
        self.db = self.client['test_db']

    def get_users_collection(self) -> AsyncMongoMockCollection:
        return self.db['users']

    def get_events_collection(self) -> AsyncMongoMockCollection:
        return self.db['events']

    def get_registrations_collection(self) -> AsyncMongoMockCollection:
        return self.db['registration']

    def get_activation_codes_collection(self) -> AsyncMongoMockCollection:
        return self.db['activation_codes']

def get_mongo_mock():
    return MockEventDatabase()