"""Конфигурация pytest и хуки для проекта EventHub API.

Модуль содержит:
- Отключение автоматической конвертации маркеров в теги Allure
- Наследование маркеров с класса на методы
- Прикрепление данных пользователя/события к отчёту при ошибках
"""

import allure
import pytest
import allure_pytest.utils as utils
from allure_commons.types import AttachmentType
from tests.core.const.allure_labels import AllureLabelApplier


applier = AllureLabelApplier(default_owner="artem")


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config):
    """Отключаем конвертацию маркеров в теги Allure."""
    def disabled_should_convert_mark_to_tag(mark):
        return False

    utils.should_convert_mark_to_tag = disabled_should_convert_mark_to_tag


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_setup(item):
    """Наследуем маркеры с класса на методы и применяем Allure метки."""
    if hasattr(item, "cls") and item.cls:
        for marker in item.cls.pytestmark:
            if not item.get_closest_marker(marker.name):
                item.add_marker(marker)

    applier.apply(item)


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Вешаем Allure тег 'slow' на медленные тесты."""

    outcome = yield
    report = outcome.get_result()


    if call.when == "call":
        duration = call.duration

        # Порог
        if duration > 0.15:
            allure.dynamic.tag("slow")

    if report.when == "call" and report.failed:
        if "user_data" in item.funcargs:
            allure.attach(
                str(item.funcargs["user_data"]),
                name="user_data_on_failure",
                attachment_type=allure.attachment_type.JSON
            )

        if "event_data" in item.funcargs:
            allure.attach(
                str(item.funcargs["event_data"]),
                name="event_data_on_failure",
                attachment_type=allure.attachment_type.JSON
            )