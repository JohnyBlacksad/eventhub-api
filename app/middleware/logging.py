"""
Middleware для логирования HTTP запросов.

Логирует каждый запрос в JSON формате для сбора Loki
"""

import time
import json
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.utils.logger import setup_logger

logger = setup_logger('eventhub.middleware')

class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware для логирования запросов.

    Логирует: метод, путь, статус, время обработки, IP клиента.
    Выводит в stdout в JSON формате.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Обработать запрос и залогировать.

        Args:
            request: FastAPI request object.
            call_next: Следующий middleware/handler

        Returns:
            Response: Ответ сервера.
        """

        start_time = time.time()
        client_host = request.client.host if request.client else 'unknown'

        response = await call_next(request)

        duration = time.time() - start_time

        logger.info(
            f"{request.method} {request.url.path}",
            extra={
                "method": request.method,
                "path": request.url.path,
                "query": str(request.url.query) if request.url.query else None,
                "status_code": response.status_code,
                "duration_ms": round(duration * 1000, 2),
                "client_ip": client_host,
                "user_agent": request.headers.get("user-agent", "unknown"),
            }
        )

        return response