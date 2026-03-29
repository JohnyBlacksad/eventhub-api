"""Главный модуль приложения EventHub API.

Точка входа FastAPI приложения. Настраивает lifespan события
для подключения к базе данных и регистрирует маршруты.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, status

from app.api.api import main_router
from app.database import db_client
from app.redis_client import redis_client
from app.middleware.request_context import RequestContextMiddleware
from app.dependency_container.activation_code_deps import get_activation_code_collection
from app.dependency_container.event_deps import get_events_collection, get_registrations_collection
from app.dependency_container.users_deps import get_user_collections
from app.middleware.logging import LoggingMiddleware
from app.models.activation_code import ActivationCodeDAO
from app.models.events import EventDAO
from app.models.registration import RegistrationDAO
from app.models.user import UserDAO
from app.migrations.runner import run_migrations
from prometheus_fastapi_instrumentator import Instrumentator, metrics
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения.

    Подключает к базе данных при старте и закрывает при остановке.
    """
    await db_client.connect()

    db = db_client.get_db()

    if db is None:
        raise RuntimeError("Database connection failed")

    await run_migrations(db)

    await EventDAO.setup_indexes(get_events_collection())
    await UserDAO.setup_indexes(get_user_collections())
    await RegistrationDAO.setup_indexes(get_registrations_collection())
    await ActivationCodeDAO.setup_indexes(get_activation_code_collection())
    await redis_client.connect()

    yield

    await redis_client.close()
    await db_client.close()

app = FastAPI(
    title="EventHub API",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc",
    openapi_url="/api/v1/openapi.json")  # redirect_slashes=True по умолчанию




@app.get("/health", tags=["System"])
async def health_check():
    """Проверить состояние приложения и базы данных.

    Returns:
        Словарь со статусом приложения и состоянием компонентов.

    Raises:
        HTTPException: Если база данных недоступна (503).
    """
    components = {'database': 'down', 'redis': 'down'}
    try:
        await db_client._ping()
        components['database'] = 'connected'
    except Exception:
        pass

    try:
        await redis_client.client.ping() # type: ignore
        components['redis'] = 'connected'
    except Exception:
        pass

    if 'down' in components.values():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={'status': 'unhealthy', 'components': components}
        )

    return {'status': 'ok', 'components': components}



app.add_middleware(LoggingMiddleware)
app.add_middleware(RequestContextMiddleware)
app.include_router(main_router, prefix="/api/v1")

instrumentator = Instrumentator(
    should_group_status_codes=False,
    should_ignore_untemplated=False,
    should_instrument_requests_inprogress=True,
    excluded_handlers=["/metrics", "/api/v1/docs", "/api/v1/redoc"],
)


instrumentator.instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)
instrumentator.add(metrics.default())

""" instrumentator.instrument(app)

@app.get("/metrics", include_in_schema=False)
async def metrics():
    # Мы берем данные именно из реестра инструментатора, а не из глобального!
    return Response(
        generate_latest(instrumentator.registry),
        media_type=CONTENT_TYPE_LATEST
    )
 """
# Metrics endpoint - добавляем напрямую после всех роутов

""" @app.get("/metrics", include_in_schema=False)
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
 """