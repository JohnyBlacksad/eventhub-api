import allure
import pytest
from allure_commons.types import AttachmentType

from tests.core.const.allure_labels import AllureLabelApplier

applier = AllureLabelApplier(default_owner="artem")


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_setup(item):
    if hasattr(item, "cls") and item.cls:
        for marker in item.cls.pytestmark:
            if not item.get_closest_marker(marker.name):
                item.add_marker(marker)

    applier.apply(item)


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()

    if report.when == "call" and report.failed:
        if "user_data" in item.funcargs:
            allure.attach(
                str(item.funcargs["user_data"]), name="user_data_on_failure", attachment_type=AttachmentType.JSON
            )

        if "event_data" in item.funcargs:
            allure.attach(
                str(item.funcargs["event_data"]), name="event_data_on_failure", attachment_type=AttachmentType.JSON
            )
