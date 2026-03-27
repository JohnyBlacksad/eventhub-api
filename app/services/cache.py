"""Сервис кэширования.

Модуль предоставляет CacheService для работы с Redis кэшем.
"""

import json
import redis.asyncio as redis
from typing import Optional, Union
from app.redis_client import redis_client
from pydantic import BaseModel, TypeAdapter

class CacheService:

    PREFIX_EVENT = 'event'
    PREFIX_USER = 'user'
    PREFIX_EVENT_LIST = 'event:list'
    PREFIX_USER_LIST = 'user:list'

    TTL_EVENT = 300
    TTL_USER = 600
    TTL_EVENT_LIST = 300
    TTL_USER_LIST = 300

    def __init__(self):
        self._redis: Optional[redis.Redis] = None

    @property
    def redis(self) -> redis.Redis:
        if self._redis is None:
            self._redis = redis_client.get_instance()

        if self._redis is None:
            raise RuntimeError("Redis client is None. Did you call redis_client.connect()?")

        return self._redis

    async def get_event(self, event_id: str):
        """Получить событие из кэша"""

        key = f'{self.PREFIX_EVENT}:{event_id}'
        cached = await self.redis.get(key)
        return json.loads(cached) if cached else None

    async def set_event(self, event_id: str, event_data: Union[BaseModel, dict]):
        """Сохранить событие в кэш"""

        key = f'{self.PREFIX_EVENT}:{event_id}'

        if isinstance(event_data, BaseModel):
            data = event_data.model_dump_json(by_alias=True)
        else:
            data = json.dumps(event_data)

        await self.redis.set(
            key,
            data,
            ex=self.TTL_EVENT,
        )

    async def delete_event(self, event_id: str):
        """Удалить событие из кэша"""

        key = f'{self.PREFIX_EVENT}:{event_id}'
        await self.redis.delete(key)

    async def get_user(self, user_id: str):
        """Получить профиль пользователя в кэш"""

        key = f'{self.PREFIX_USER}:{user_id}'
        cached = await self.redis.get(key)

        return json.loads(cached) if cached else None

    async def set_user(self, user_id: str, user_data: Union[BaseModel, dict]):
        """Сохранить профиль пользователя в кэш"""

        key = f'{self.PREFIX_USER}:{user_id}'

        if isinstance(user_data, BaseModel):
            data = user_data.model_dump_json(by_alias=True)
        else:
            data = json.dumps(user_data)

        await self.redis.set(
            key,
            data,
            ex=self.TTL_USER,
        )

    async def delete_user(self, user_id: str):
        """Удалить пользователя из кэша"""

        key = f'{self.PREFIX_USER}:{user_id}'
        await self.redis.delete(key)

    async def get_event_list(self, filters_hash: str):
        """Получить список событий из кэша"""

        key = f'{self.PREFIX_EVENT_LIST}:{filters_hash}'
        cached = await self.redis.get(key)
        return json.loads(cached) if cached else None

    async def set_events_list(self, filters_hash: str, events: Union[BaseModel, list]):
        """Сохранить список событий в кэш"""

        key = f'{self.PREFIX_EVENT_LIST}:{filters_hash}'

        if isinstance(events, BaseModel):
            data = events.model_dump_json(by_alias=True)
        elif isinstance(events, list):
            data = TypeAdapter(list).dump_json(events, by_alias=True).decode()
        else:
            data = json.dumps(events)

        await self.redis.set(
            key,
            data,
            ex=self.TTL_EVENT_LIST,
        )

    async def delete_event_list(self):
        """Удалить весь кэш событий"""

        pattern = f'{self.PREFIX_EVENT_LIST}:*'
        keys = []

        async for key in self.redis.scan_iter(match=pattern):
            keys.append(key)

        if keys:
            await self.redis.delete(*keys)

    async def get_user_list(self, filters_hash: str):
        """Получить список пользователей"""

        key = f'{self.PREFIX_USER_LIST}:{filters_hash}'
        cached = await self.redis.get(key)
        return json.loads(cached) if cached else None


    async def set_user_list(self, filters_hash: str, users: Union[BaseModel, list]):
        """Сохранить список пользователей в кэш"""

        key = f'{self.PREFIX_USER_LIST}:{filters_hash}'

        if isinstance(users, BaseModel):
            data = users.model_dump_json(by_alias=True)
        elif isinstance(users, list):
            data = TypeAdapter(list).dump_json(users, by_alias=True).decode()
        else:
            data = json.dumps(users)

        await self.redis.set(
            key,
            data,
            ex=self.TTL_USER_LIST
        )

    async def delete_user_list(self):
        """Удалить весь кэш пользователей"""

        pattern = f'{self.PREFIX_USER_LIST}:*'
        keys = []

        async for key in self.redis.scan_iter(match=pattern):
            keys.append(key)

        if keys:
            await self.redis.delete(*keys)

    async def clear_all(self):
        """Удалить весь кэш"""

        await self.redis.flushall()

    async def health_check(self) -> bool:
        """Проверить подключение к Redis"""
        if self._redis is None:
            return False
        try:
            await self._redis.ping()  # type: ignore[union-attr]
            return True
        except Exception:
            return False

cache_service = CacheService()