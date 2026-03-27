"""Настройки и константы для TaskIQ очередей"""

class TaskQueueSettings:
    """Константы для очередей задач."""

    QUEUE_MAIN = "eventhub:queue:main"
    QUEUE_CLEANUP = "eventhub:queue:cleanup"
    QUEUE_NOTIFICATION = "eventhub:queue:notification"
    QUEUE_CACHE = "eventhub:queue:cache"

    DEFAULT_TIMEOUT = 300
    CLEANUP_TIMEOUT = 600
    NOTIFICATION_TIMEOUT = 60
    CACHE_TIMEOUT = 30

    MAX_RETRIES = 3
    RETRY_DELAY = 5