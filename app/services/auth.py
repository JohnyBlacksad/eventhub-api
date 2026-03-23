"""Сервис аутентификации.

Модуль содержит AuthService для работы с JWT токенами
и хеширования паролей.
"""

from datetime import datetime, timedelta, timezone

import jwt
from fastapi import HTTPException, status
from fastapi.concurrency import run_in_threadpool
from passlib.context import CryptContext

from app.config import settings


class AuthService:
    """Сервис для работы с JWT токенами и хеширования паролей.

    Использует bcrypt для хеширования паролей и PyJWT для работы
    с JWT токенами. Все методы асинхронные для интеграции с FastAPI.

    Атрибуты:
        pwd_context: CryptContext для bcrypt хеширования.
        secret_key: Секретный ключ для подписи JWT токенов (bytes).
        algorithm: Алгоритм подписи JWT (HS256).
    """

    def __init__(self):
        """Инициализация AuthService.

        Загружает настройки из app.config.settings:
        - crypto_schemas: схема хеширования (bcrypt)
        - secret_key: секретный ключ для JWT
        - algorithm: алгоритм подписи (HS256)
        """
        self.pwd_context = CryptContext(schemes=[settings.auth_config.crypto_schemas], deprecated="auto")
        self.secret_key = settings.auth_config.secret_key.encode()
        self.algorithm = settings.auth_config.algorithm

    async def hash_password(self, password: str) -> str:
        """Захешировать пароль используя bcrypt.

        Args:
            password: Пароль в открытом виде.

        Returns:
            Хешированная строка пароля.

        Example:
            >>> await auth_service.hash_password("mypassword123")
            '$2b$12$Kx8...9zQ'
        """
        return await run_in_threadpool(self.pwd_context.hash, password)

    async def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Проверить соответствие пароля хешу.

        Args:
            plain_password: Пароль в открытом виде.
            hashed_password: Хешированная строка для проверки.

        Returns:
            True если пароль соответствует хешу, False иначе.

        Example:
            >>> await auth_service.verify_password("mypassword123", "$2b$12$Kx8...9zQ")
            True
        """
        return await run_in_threadpool(self.pwd_context.verify, plain_password, hashed_password)

    async def create_access_token(self, data: dict) -> str:
        """Создать JWT access токен.

        Args:
            data: Данные для кодирования (обычно user_id, email).

        Returns:
            JWT токен в виде строки.

        Note:
            Время жизни токена: settings.auth_config.access_token_expire_time (30 мин).
            Добавляет поле 'exp' (expiration) автоматически.

        Example:
            >>> await auth_service.create_access_token({"user_id": "123", "email": "user@example.com"})
            'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'
        """
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.auth_config.access_token_expire_time)
        to_encode.update({"exp": expire})
        token = await run_in_threadpool(jwt.encode, to_encode, self.secret_key, algorithm=self.algorithm)
        return token

    async def create_refresh_token(self, data: dict) -> str:
        """Создать JWT refresh токен.

        Args:
            data: Данные для кодирования (обычно user_id, email).

        Returns:
            JWT токен в виде строки.

        Note:
            Время жизни токена: settings.auth_config.refresh_token_expire_time (7 дней).
            Добавляет поле 'exp' (expiration) автоматически.

        Example:
            >>> await auth_service.create_refresh_token({"user_id": "123", "email": "user@example.com"})
            'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'
        """
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(days=settings.auth_config.refresh_token_expire_time)
        to_encode.update({"exp": expire})
        refresh_token = await run_in_threadpool(jwt.encode, to_encode, self.secret_key, algorithm=self.algorithm)
        return refresh_token

    async def decode_token(self, token: str) -> dict:
        """Декодировать и проверить JWT токен.

        Args:
            token: JWT токен в виде строки.

        Returns:
            Декодированные данные токена (payload).

        Raises:
            HTTPException: 401 если токен истёк (ExpiredSignatureError).
            HTTPException: 401 если токен невалиден (InvalidTokenError).

        Example:
            >>> await auth_service.decode_token("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...")
            {'user_id': '123', 'email': 'user@example.com', 'exp': 1710234567}
        """
        try:
            payload = await run_in_threadpool(jwt.decode, token, self.secret_key, algorithms=[self.algorithm])
            return payload

        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
