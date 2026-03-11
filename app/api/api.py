"""API роуты.

Модуль содержит главный роутер для всех endpoints приложения.
"""

from fastapi import APIRouter
from app.api.routes.auth import auth_router

main_router = APIRouter()

main_router.include_router(auth_router, prefix='/auth', tags=['Auth'])