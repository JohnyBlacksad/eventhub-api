"""API роуты.

Модуль содержит главный роутер для всех endpoints приложения.
"""

from fastapi import APIRouter
from app.api.routes.auth import auth_router
from app.api.routes.users import user_router
from app.api.routes.events import event_router
from app.api.routes.admin import admin_route

main_router = APIRouter()

main_router.include_router(auth_router, prefix='/auth', tags=['Auth'])
main_router.include_router(user_router, prefix='/users', tags=['Users'])
main_router.include_router(event_router, prefix='/events', tags=['Events'])
main_router.include_router(admin_route, prefix='/admin', tags=['Admin'])