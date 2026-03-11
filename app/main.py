"""Главный модуль приложения EventHub API.

Точка входа FastAPI приложения. Настраивает lifespan события
для подключения к базе данных и регистрирует маршруты.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, status, HTTPException
from app.database import db_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения.

    Подключает к базе данных при старте и закрывает при остановке.
    """
    await db_client.connect()
    yield
    await db_client.close()


app = FastAPI(
    title='EventHub API',
    version='0.1.0',
    lifespan=lifespan)


@app.get('/api/v1/health', tags=['System'])
async def health_check():
    """Проверить состояние приложения и базы данных.

    Returns:
        Словарь со статусом приложения и состоянием компонентов.

    Raises:
        HTTPException: Если база данных недоступна (503).
    """
    try:
        await db_client._ping()
        return {
            'status': 'ok',
            'components': {
                'database': "connected",
            }
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                            detail=f'Database is down: {e}')