"""Подключение к Redis

Класс RedisClient для управления
подключением к Redis через aioredis

"""

import redis.asyncio as redis
from redis.asyncio.retry import Retry
from redis.backoff import ExponentialBackoff
from typing import Optional

from app.config import settings

from app.utils.logger import get_logger
from app.config_models.loggers_enum import LoggerName

logger = get_logger(LoggerName.REDIS_LOGGER)

class RedisClient:
    """
    Класс для управления подключением к Redis.
    """

    def __init__(self):
        self._pool: Optional[redis.ConnectionPool] = None
        self.client: Optional[redis.Redis] = None

    async def connect(self):
        """Инициализация пула и проверка связи."""
        retry = Retry(ExponentialBackoff(), 5)  # 5 попыток

        self._pool = redis.ConnectionPool.from_url(
            url=settings.redis_config.url,
            db=settings.redis_config.db,
            password=settings.redis_config.password,
            decode_responses=True,
            max_connections=20,
            socket_timeout=10.0,         # 10 секунд
            socket_connect_timeout=10.0, # 10 секунд
            retry=retry,
            retry_on_timeout=True
        )

        self.client = redis.Redis(connection_pool=self._pool)

        try:
            await self.client.ping() # type: ignore
            logger.debug("Redis Service connected", extra={
                "url": settings.redis_config.url,
                "database": settings.redis_config.db,
            })
        except Exception as e:
            logger.error("Reis Service connected error", extra={
                "url": settings.redis_config.url,
                "database": settings.redis_config.db,
                "error": str(e),
            })
            raise ConnectionError(f'Could not connect to Redis at {settings.redis_config.url}: {e}')

    async def close(self):
        """Закрыть подключение к Redis"""
        logger.debug("Redis Service disconnect", extra={
                "url": settings.redis_config.url,
                "database": settings.redis_config.db,
            })

        if self._pool:
            await self._pool.disconnect()

    def get_instance(self):
        if self.client is None:
            raise RuntimeError("RedisClient is not connected. Call connect() first.")
        return self.client

redis_client = RedisClient()