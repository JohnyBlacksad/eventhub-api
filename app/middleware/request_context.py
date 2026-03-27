"""Middleware для добавления trace_id к каждому запросу"""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response
from starlette.types import ASGIApp, Receive, Scope, Send
from app.utils.logger import set_trace_id, trace_id_var

class RequestContextMiddleware(BaseHTTPMiddleware):
    """Middleware для добавления trace_id к каждому запросу.

    Извлекает trace_id из заголовка X-Trace-ID или генерирует новый.
    Добавляет trace_id в ответ и контекст логгера.
    """

    async def dispatch(self, request: Request, call_next):
        """Добавить trace_id к запросу и логам

        Args:
            request: HTTP заголовок
            call_next: Следующий middleware/handler

        Returns:
            HTTP ответ с заголовком X-Trace-ID.
        """

        trace_id_header = request.headers.get("X-Trace-ID")

        trace_id, token = set_trace_id(trace_id_header)

        try:
            response = await call_next(request)
            response.headers["X-Trace-ID"] = trace_id
            return response
        finally:
            trace_id_var.reset(token)