from mock import patch

from scripts.c2r_script import run_convert2rhel


@patch("scripts.c2r_script.SCRIPT_TYPE", "ANALYSIS")
@patch("scripts.c2r_script.IS_ANALYSIS", True)
def test_run_convert2rhel_custom_variables():
    mock_env = {"FOO": "BAR", "BAR": "BAZ", "RHC_WORKER_LALA": "LAND"}

    with patch("os.environ", mock_env), patch(
        "scripts.c2r_script.run_subprocess", return_value=(b"", 0)
    ) as mock_popen:
        run_convert2rhel()

    mock_popen.assert_called_once_with(
        ["/usr/bin/convert2rhel", "analyze", "-y"],
        env={"FOO": "BAR", "BAR": "BAZ", "LALA": "LAND"},
    )


@patch("scripts.c2r_script.SCRIPT_TYPE", "CONVERSION")
def test_run_convert2rhel_conversion():
    mock_env = {
        "PATH": "/fake/path",
        "RHC_WORKER_CONVERT2RHEL_DISABLE_TELEMETRY": "1",
        "RHC_WORKER_FOO": "1",
    }

    with patch("os.environ", mock_env), patch(
        "scripts.c2r_script.run_subprocess", return_value=(b"", 0)
    ) as mock_popen:
        run_convert2rhel()

    mock_popen.assert_called_once_with(
        ["/usr/bin/convert2rhel", "-y"],
        env={
            "PATH": "/fake/path",
            "CONVERT2RHEL_DISABLE_TELEMETRY": "1",
            "FOO": "1",
        },
    )


@patch("scripts.c2r_script.SCRIPT_TYPE", "ANALYSIS")
@patch("scripts.c2r_script.IS_ANALYSIS", True)
def test_run_convert2rhel_analysis():
    mock_env = {"PATH": "/fake/path", "RHC_WORKER_CONVERT2RHEL_DISABLE_TELEMETRY": "1"}

    with patch("os.environ", mock_env), patch(
        "scripts.c2r_script.run_subprocess", return_value=(b"", 0)
    ) as mock_popen:
        run_convert2rhel()

    mock_popen.assert_called_once_with(
        ["/usr/bin/convert2rhel", "analyze", "-y"],
        env={"PATH": "/fake/path", "CONVERT2RHEL_DISABLE_TELEMETRY": "1"},
    )
