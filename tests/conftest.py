import allure
import pytest
from tests.core.const.allure_labels import AllureLabelApplier
from allure_commons.types import AttachmentType

applier = AllureLabelApplier(default_owner="artem")

@pytest.hookimpl(tryfirst=True)
def pytest_runtest_setup(item):
    applier.apply(item)


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()

    if report.when == 'call' and report.failed:
        if 'user_data' in item.funcargs:
            allure.attach(
                str(item.funcargs['user_data']),
                name='user_data_on_failure',
                attachment_type=AttachmentType.JSON
            )

        if 'event_data' in item.funcargs:
            allure.attach(
                str(item.funcargs['event_data']),
                name='event_data_on_failure',
                attachment_type=AttachmentType.JSON
            )