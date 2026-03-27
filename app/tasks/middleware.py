"""Middleware для TaskIQ для propagation trace_id"""


from collections.abc import Coroutine
from types import CoroutineType
from typing import Any

from taskiq import (
    TaskiqMessage,
    TaskiqState,
    TaskiqMiddleware
)

from app.utils.logger import set_trace_id

class TraceIdMiddleware(TaskiqMiddleware):
    """Middleware для извлечения trace_id из задач."""

    async def pre_execute(self, message: TaskiqMessage) -> TaskiqMessage:
        """Извлечь trace_id перед выполнением задачи."""
        trace_id = message.labels.get("trace_id")
        if trace_id:
            set_trace_id(trace_id)

        return message