from enum import StrEnum

class LoggerName(StrEnum):
    AUTH_SERVICE_LOGGER = "eventhub.services.auth"
    USER_SERVICE_LOGGER = "eventhub.services.user"
    EVENT_SERVICE_LOGGER = "eventhub.services.event"
    ACTIVATION_CODE_LOGGER = "eventhub.services.activation_code"

    USER_DAO_LOGGER = "eventhub.dao.user"
    REGISTRATION_DAO_LOGGER = "eventhub.dao.registration"
    EVENT_DAO_LOGGER = "eventhub.dao.event"
    ACTIVATION_CODE_DAO_LOGGER = "eventhub.dao.activation_code"

    DATA_BASE_LOGGER = "eventhub.database"
    REDIS_LOGGER = "eventh.redis"

    QUEUE_TASK_NOTIFICATION_LOGGER = "eventhub.task.notification"
    QUEUE_TASK_CLEANUP_LOGGER = "eventhub.task.cleanup"
    QUEUE_TASK_CACHE_LOGGER = "eventhub.task.cache"

    HTTP_MIDDLEWARE_LOGGER  = "eventhub.http"