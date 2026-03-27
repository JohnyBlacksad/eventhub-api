"""Точка входа для TaskIQ воркера.

Запуск:
    taskiq worker app.task.worker:broker
"""

import asyncio
import signal
import sys

from app.tasks.broker import broker


def main():
    """Запустить воркер"""

    def handle_signal(signum, frame):
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

if __name__ == "__main__":
    main()