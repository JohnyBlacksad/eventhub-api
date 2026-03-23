from abc import ABC, abstractmethod
from motor.motor_asyncio import AsyncIOMotorDatabase


class Migration(ABC):
    '''Базовый класс для всех миграций'''

    version: str = '000'
    name: str = ''

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    @abstractmethod
    async def up(self) -> None:
        'Применить миграцию'

    async def down(self) -> None:
        'Откатить миграцию (опционально)'
        pass