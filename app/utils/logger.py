"""
Настройка логгера для приложения.

Логгирует в JSON формате для совместимости с Loki.
"""

import json
import logging
import sys
import uuid
from typing import Any
from contextvars import ContextVar
from app.config import settings


trace_id_var: ContextVar[str] = ContextVar('trace_id', default='')

def set_trace_id(trace_id: str | None = None) -> tuple[str, Any]:
    """Установить trace_id в контекст.
    Args:
        trace_id: Trace ID (Если None - сгенерируется новый)
    Returns:
        str: Установленный Trace ID
    """

    if trace_id is None:
        trace_id = str(uuid.uuid4())
    token = trace_id_var.set(trace_id)
    return trace_id, token

def get_trace_id() -> str:
    """Получить текущий Trace ID из контекста
    Returns:
        str: Текущий trace_id
    """
    return trace_id_var.get()

def get_logger(name: str) -> logging.Logger:
    """Получить логгер с JSON форматтером.
    Args:
        name: Имя логгера
    Returns:
        Logger: Настроенный логгер.
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, settings.log_level.upper()))

    if logger.handlers:
        return logger

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(getattr(logging, settings.log_level.upper()))

    formatter = JSONFormatter()
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    logger.propagate = False

    return logger


class JSONFormatter(logging.Formatter):
    """
    Форматтер для вывода логов в JSON формате.
    """

    def format(self, record: logging.LogRecord) -> str:
        """
        Преобразовать лог в записть JSON.

        Args:
            record: Лог запись от logging модуля.

        Returns:
            JSON строка с данными лога.
        """

        log_data: dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "service": "api",
            "trace_id": get_trace_id(),
        }

        skip_attrs = {
            "name",
            "msg",
            "args",
            "created",
            "filename",
            "funcName",
            "levelname",
            "levelno",
            "lineno",
            "module",
            "msecs",
            "pathname",
            "process",
            "processName",
            "relativeCreated",
            "stack_info",
            "exc_info",
            "exc_text",
            "thread",
            "threadName",
            "message",
            "asctime",
            "logger",
            "service",
            "trace_id",
        }

        for key, value in record.__dict__.items():
            if key not in skip_attrs:
                log_data[key] = value

        if record.exc_info:
            log_data["exc_info"] = self.formatException(record.exc_info)

        return json.dumps(log_data, ensure_ascii=False, default=str)


def setup_logger(name: str = "eventhub", level: int = logging.INFO) -> logging.Logger:
    """
    Настроить логгер с JSON форматтером.

    Args:
        name: Имя логгера.
        level: Уровень логгирования (INFO, DEBUG, etc.)

    Returns:
        Logger: Настроенный логгер.
    """

    logger = logging.getLogger(name)
    logger.setLevel(level)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)

    formatter = JSONFormatter()
    handler.setFormatter(formatter)

    logger.addHandler(handler)

    logger.propagate = False

    return logger
