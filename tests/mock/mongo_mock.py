"""Мок объекты MongoDB для тестирования.

Модуль содержит класс MockEventDatabase который предоставляет
асинхронные мок коллекции MongoDB используя mongomock-motor.

Используется в тестах DAO слоя для изоляции от реальной БД.
"""

from mongomock_motor import AsyncMongoMockClient, AsyncMongoMockCollection


class MockEventDatabase:
    """Мок база данных MongoDB для тестов.

    Предоставляет мок коллекции для users, events, registrations, activation_codes.
    Все коллекции асинхронные и совместимы с Motor API.

    Attributes:
        client: AsyncMongoMockClient — Мок клиент MongoDB.
        db: База данных с тестовыми коллекциями.
    """

    def __init__(self):
        """Инициализировать мок клиент MongoDB."""
        self.client = AsyncMongoMockClient()
        self.db = self.client["test_db"]

    def get_users_collection(self) -> AsyncMongoMockCollection:
        """Получить мок коллекцию users.

        Returns:
            AsyncMongoMockCollection: Мок коллекция пользователей.
        """
        return self.db["users"]

    def get_events_collection(self) -> AsyncMongoMockCollection:
        """Получить мок коллекцию events.

        Returns:
            AsyncMongoMockCollection: Мок коллекция событий.
        """
        return self.db["events"]

    def get_registrations_collection(self) -> AsyncMongoMockCollection:
        """Получить мок коллекцию registrations.

        Returns:
            AsyncMongoMockCollection: Мок коллекция регистраций.
        """
        return self.db["registration"]

    def get_activation_codes_collection(self) -> AsyncMongoMockCollection:
        """Получить мок коллекцию activation_codes.

        Returns:
            AsyncMongoMockCollection: Мок коллекция кодов активации.
        """
        return self.db["activation_codes"]


def get_mongo_mock():
    """Создать экземпляр мок базы данных.

    Returns:
        MockEventDatabase: Экземпляр мок базы данных.
    """
    return MockEventDatabase()
