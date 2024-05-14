from mock import patch

import pytest
from convert2rhel_insights_tasks.main import generate_report_message


@pytest.mark.parametrize(
    ("highest_status", "expected_message", "has_alert"),
    [
        (
            "SUCCESS",
            (
                "No problems found. The system was converted successfully. Please,"
                " reboot your system at your earliest convenience to make sure that"
                " the system is using the RHEL Kernel."
            ),
            False,
        ),
        (
            "INFO",
            (
                "No problems found. The system was converted successfully. Please,"
                " reboot your system at your earliest convenience to make sure that"
                " the system is using the RHEL Kernel."
            ),
            False,
        ),
        (
            "WARNING",
            (
                "No problems found. The system was converted successfully. Please,"
                " reboot your system at your earliest convenience to make sure that"
                " the system is using the RHEL Kernel."
            ),
            False,
        ),
        (
            "ERROR",
            "The conversion cannot proceed. You must resolve existing issues to perform the conversion.",
            True,
        ),
    ],
)
@patch("convert2rhel_insights_tasks.main.SCRIPT_TYPE", "CONVERSION")
@patch("convert2rhel_insights_tasks.main.IS_CONVERSION", True)
def test_generate_report_message_conversion(
    highest_status,
    expected_message,
    has_alert,
):
    assert generate_report_message(highest_status) == (
        expected_message,
        has_alert,
    )


@pytest.mark.parametrize(
    "highest_status, expected_message, has_alert",
    [
        ("SUCCESS", "No problems found. The system is ready for conversion.", False),
        ("INFO", "No problems found. The system is ready for conversion.", False),
        (
            "WARNING",
            "The conversion can proceed. However, "
            "there is one or more warnings about issues that might occur after the conversion.",
            False,
        ),
        (
            "SKIP",
            "The conversion cannot proceed. You must resolve existing issues to perform the conversion.",
            True,
        ),
        (
            "OVERRIDABLE",
            "The conversion cannot proceed. You must resolve existing issues to perform the conversion.",
            True,
        ),
        (
            "ERROR",
            "The conversion cannot proceed. You must resolve existing issues to perform the conversion.",
            True,
        ),
    ],
)
@patch("convert2rhel_insights_tasks.main.SCRIPT_TYPE", "ANALYSIS")
@patch("convert2rhel_insights_tasks.main.IS_ANALYSIS", True)
def test_generate_report_message_analysis(highest_status, expected_message, has_alert):
    assert generate_report_message(highest_status) == (expected_message, has_alert)
