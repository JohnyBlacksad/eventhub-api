from enum import Enum


class BaseMarkerEnum(Enum):
    """
    Базовый класс для всех енумов, используемых в маркерах тестов
    Автоматически регистрирует все свои подклассы.
    """

    __registry = set()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if cls is not BaseMarkerEnum:
            BaseMarkerEnum.__registry.add(cls)

    @classmethod
    def get_all(cls):
        """Возвращает список всех зарегистрированных классов enum'ов."""
        return list(cls.__registry)


def _register_all_enums():
    """Принудительно зарегистрировать все enum'ы."""
    from tests.core.const import mark_enums # noqa: F401


_register_all_enums()
