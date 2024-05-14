import pytest
from mock import patch, call

from convert2rhel_insights_tasks.main import (
    install_or_update_convert2rhel,
    ProcessError,
)


@pytest.mark.parametrize(
    ("subprocess_mock", "pkg_installed_mock", "should_undo_transaction"),
    (
        ((b"output", 0), False, True),
        ((b"output", 0), True, False),
    ),
)
def test_install_or_update_convert2rhel(
    subprocess_mock, pkg_installed_mock, should_undo_transaction
):
    with patch(
        "convert2rhel_insights_tasks.main.run_subprocess",
        return_value=subprocess_mock,
    ) as mock_run_subprocess:
        with patch(
            "convert2rhel_insights_tasks.main._check_if_package_installed",
            return_value=pkg_installed_mock,
        ) as mock_run_pkg_check:
            with patch(
                "convert2rhel_insights_tasks.main.setup_convert2rhel",
                return_value=pkg_installed_mock,
            ) as mock_download_files:
                with patch(
                    "convert2rhel_insights_tasks.main._get_last_yum_transaction_id",
                    return_value=1,
                ) as mock_transaction_get:
                    should_undo, _ = install_or_update_convert2rhel([])

    assert should_undo is should_undo_transaction
    mock_run_pkg_check.assert_called_once()
    mock_run_subprocess.assert_called_once()
    assert mock_transaction_get.call_count == (0 if pkg_installed_mock else 1)

    if pkg_installed_mock:
        mock_download_files.assert_not_called()
        expected_calls = [
            ["/usr/bin/yum", "update", "convert2rhel", "-y"],
        ]
    else:
        mock_download_files.assert_called_once()
        expected_calls = [["/usr/bin/yum", "install", "convert2rhel", "-y"]]

    assert mock_run_subprocess.call_args_list == [call(args) for args in expected_calls]


@patch(
    "convert2rhel_insights_tasks.main._check_if_package_installed", return_value=False
)
@patch("convert2rhel_insights_tasks.main.run_subprocess", return_value=(b"failed", 1))
def test_install_or_update_convert2rhel_raise_exception(
    mock_run_subprocess, mock_pkg_check
):
    with pytest.raises(
        ProcessError,
        match="Installing convert2rhel with yum exited with code '1' and output:\nfailed",
    ):
        install_or_update_convert2rhel([])

    expected_calls = [["/usr/bin/yum", "install", "convert2rhel", "-y"]]

    mock_pkg_check.assert_called_once()
    assert mock_run_subprocess.call_args_list == [call(args) for args in expected_calls]


@patch(
    "convert2rhel_insights_tasks.main._check_if_package_installed", return_value=True
)
@patch("convert2rhel_insights_tasks.main.run_subprocess", return_value=(b"failed", 1))
def test_update_convert2rhel_raise_exception(mock_run_subprocess, mock_pkg_check):
    with pytest.raises(
        ProcessError,
        match="Updating convert2rhel with yum exited with code '1' and output:\nfailed",
    ):
        install_or_update_convert2rhel([])

    expected_calls = [
        ["/usr/bin/yum", "update", "convert2rhel", "-y"],
    ]

    mock_pkg_check.assert_called_once()
    assert mock_run_subprocess.call_args_list == [call(args) for args in expected_calls]
