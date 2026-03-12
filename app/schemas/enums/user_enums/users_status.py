"""Перечисления пользователей.

Модуль содержит Enum для ролей пользователей.
"""

from enum import StrEnum


class UserRoleEnum(StrEnum):
    """Роли пользователей в системе.

    Значения:
        USER: Обычный пользователь.
        ADMIN: Администратор с расширенными правами.
    """
    USER = 'user'
    ADMIN = 'admin'
    ORGANIZER = 'organizer'