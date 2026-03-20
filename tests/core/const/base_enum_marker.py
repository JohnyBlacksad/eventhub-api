"""Базовый класс для enum'ов с маркерами pytest.

Модуль содержит:
- BaseMarkerEnum — базовый класс который автоматически регистрирует все подклассы
- Механизм для автоматического обнаружения всех enum'ов с маркерами
- Функцию _register_all_enums() для принудительной регистрации

Используется в AllureLabelApplier для применения меток на основе маркеров.
"""

from enum import Enum


class BaseMarkerEnum(Enum):
    """Базовый класс для всех enum'ов, используемых в маркерах тестов.

    Автоматически регистрирует все свои подклассы в __registry для последующего
    использования в AllureLabelApplier.

    Class Attributes:
        __registry: set — Набор всех зарегистрированных подклассов.
    """

    __registry = set()

    def __init_subclass__(cls, **kwargs):
        """Автоматически вызывается при создании подкласса.

        Добавляет подкласс в реестр если это не сам BaseMarkerEnum.
        """
        super().__init_subclass__(**kwargs)
        if cls is not BaseMarkerEnum:
            BaseMarkerEnum.__registry.add(cls)

    @classmethod
    def get_all(cls):
        """Вернуть список всех зарегистрированных классов enum'ов.

        Returns:
            list: Список классов подклассов BaseMarkerEnum.
        """
        return list(cls.__registry)


def _register_all_enums():
    """Принудительно зарегистрировать все enum'ы импортируя mark_enums.

    Вызывается при загрузке модуля для обеспечения регистрации всех enum'ов
    до создания AllureLabelApplier.
    """
    from tests.core.const import mark_enums  # noqa: F401


_register_all_enums()
