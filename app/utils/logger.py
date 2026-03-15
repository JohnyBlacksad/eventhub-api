"""
Настройка логгера для приложения.

Логгирует в JSON формате для совместимости с Loki.
"""

import logging
import sys
import json
from typing import Any



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
        }

        skip_attrs = {
            'name', 'msg', 'args', 'created', 'filename', 'funcName',
            'levelname', 'levelno', 'lineno', 'module', 'msecs',
            'pathname', 'process', 'processName', 'relativeCreated',
            'stack_info', 'exc_info', 'exc_text', 'thread', 'threadName',
            'message', 'asctime', 'logger'
        }

        for key, value in record.__dict__.items():
            if key not in skip_attrs:
                log_data[key] = value

        if record.exc_info:
            log_data['exc_info'] = self.formatException(record.exc_info)

        return json.dumps(log_data)

def setup_logger(name: str = 'eventhub', level: int = logging.INFO) -> logging.Logger:
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
