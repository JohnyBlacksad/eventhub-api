"""Главный модуль приложения EventHub API.

Точка входа FastAPI приложения. Настраивает lifespan события
для подключения к базе данных и регистрирует маршруты.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, status, HTTPException
from app.database import db_client
from app.dependency_container.users_deps import get_user_collections
from app.dependency_container.event_deps import (
    get_events_collection,
    get_registrations_collection)
from app.dependency_container.activation_code_deps import get_activation_code_collection
from app.models.user import UserDAO
from app.models.events import EventDAO
from app.models.registration import RegistrationDAO
from app.models.activation_code import ActivationCodeDAO
from app.api.api import main_router
from app.middleware.logging import LoggingMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения.

    Подключает к базе данных при старте и закрывает при остановке.
    """
    await db_client.connect()

    user_collection = get_user_collections()
    event_collection = get_events_collection()
    registrations_collection = get_registrations_collection()
    activation_code_collection = get_activation_code_collection()

    await EventDAO.setup_indexes(event_collection)
    await UserDAO.setup_indexes(user_collection)
    await RegistrationDAO.setup_indexes(registrations_collection)
    await ActivationCodeDAO.setup_indexes(activation_code_collection)

    yield

    await db_client.close()


app = FastAPI(
    title='EventHub API',
    version='0.1.0',
    lifespan=lifespan)  # redirect_slashes=True по умолчанию



@app.get('/health', tags=['System'])
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
                'database': 'connected',
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f'Database is down: {e}'
        )

app.add_middleware(LoggingMiddleware)
app.include_router(main_router, prefix='/api/v1')
