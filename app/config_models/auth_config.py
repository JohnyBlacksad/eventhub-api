"""Модели конфигурации аутентификации.

Модуль содержит Pydantic модели для настроек JWT и хеширования.
"""

from pydantic import BaseModel


class AuthConfig(BaseModel):
    """Настройки аутентификации.

    Атрибуты:
        crypto_schemas: Схема хеширования паролей (bcrypt).
        secret_key: Секретный ключ для подписи JWT токенов.
        algorithm: Алгоритм подписи JWT (HS256).
        access_token_expire_time: Время жизни access токена (минуты).
        refresh_token_expire_time: Время жизни refresh токена (дни).
    """

    crypto_schemas: str
    secret_key: str
    algorithm: str
    access_token_expire_time: int
    refresh_token_expire_time: int
