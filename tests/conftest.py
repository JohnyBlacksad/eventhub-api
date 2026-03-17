import allure
import pytest
from tests.core.const.mark_enums import (
    MarkTests,
    ModuleMarks,
    ServicesMark,
    FeaturesUserMark,
    DataBaseFunctionMark
)

@pytest.hookimpl(tryfirst=True)
def pytest_runtest_setup(item):
    test_marks = [marker.name for marker in item.iter_markers()]

    if MarkTests.UNITS in test_marks:
        allure.dynamic.epic("Unit Tests")

    if ServicesMark.USERS in test_marks:
        allure.dynamic.feature("Service: USERS")
    elif ServicesMark.EVENTS in test_marks:
        allure.dynamic.feature("Service: EVENTS")

    if ModuleMarks.DAO in test_marks:
        allure.dynamic.story("Data Access Layer (DAO)")

    user_features = {f.value for f in FeaturesUserMark}
    db_functions = {f.value for f in DataBaseFunctionMark}

    for mark_name in test_marks:
        if mark_name in user_features or mark_name in db_functions:

            allure.dynamic.label("feature_action", mark_name)
            allure.dynamic.tag(mark_name)

import allure
from allure_commons.types import AttachmentType

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()

    if report.when == 'call' and report.failed:
        if 'user_data' in item.funcargs:
            allure.attach(
                str(item.funcargs['user_data']),
                name="user_data_on_failure",
                attachment_type=AttachmentType.JSON
            )