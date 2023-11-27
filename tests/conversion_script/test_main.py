# pylint: disable=too-many-arguments

from mock import patch, mock_open, Mock

from scripts.conversion_script import main, ProcessError, OutputCollector


@patch(
    "scripts.conversion_script.get_system_distro_version", return_value=("centos", "7")
)
@patch("scripts.conversion_script.is_non_eligible_releases", return_value=True)
@patch("scripts.conversion_script.cleanup")
@patch("scripts.conversion_script.OutputCollector")
def test_main_non_eligible_release(
    mock_output_collector,
    mock_cleanup,
    mock_is_non_eligible_releases,
    mock_get_system_distro_version,
):
    mock_output_collector.return_value = OutputCollector(entries=["non-empty"])

    main()

    mock_get_system_distro_version.assert_called_once()
    mock_is_non_eligible_releases.assert_called_once()
    mock_output_collector.assert_called()
    mock_cleanup.assert_called_once()


# fmt: off
@patch("scripts.conversion_script.gather_json_report", side_effect=[{"actions": []}])
@patch("scripts.conversion_script.update_insights_inventory", side_effect=Mock())
@patch("scripts.conversion_script.setup_convert2rhel", side_effect=Mock())
@patch("scripts.conversion_script.install_convert2rhel", return_value=(True, 1))
@patch("scripts.conversion_script.check_convert2rhel_inhibitors_before_run", return_value=("", 0))
@patch("scripts.conversion_script.run_convert2rhel", side_effect=Mock())
@patch("scripts.conversion_script.find_highest_report_level", side_effect=Mock(return_value=["SUCCESS"]))
@patch("scripts.conversion_script.gather_textual_report", side_effect=Mock(return_value=""))
@patch("scripts.conversion_script.generate_report_message", side_effect=Mock(return_value=("successfully", False)))
@patch("scripts.conversion_script.transform_raw_data", side_effect=Mock(return_value=""))
# These patches are calls made in cleanup
@patch("os.path.exists", return_value=False)
@patch("scripts.conversion_script._create_or_restore_backup_file", side_effect=Mock())
@patch("scripts.conversion_script.run_subprocess", return_value=("", 1))
@patch("scripts.conversion_script.get_system_distro_version", return_value=("centos", "7"))
@patch("scripts.conversion_script.is_non_eligible_releases", return_value=False)
# fmt: on
def test_main_success_c2r_installed(
    mock_is_non_eligible_releases,
    mock_get_system_distro_version,
    mock_cleanup_pkg_call,
    mock_cleanup_file_restore_call,
    mock_cleanup_file_exists_call,
    mock_transform_raw_data,
    mock_generate_report_message,
    mock_gather_textual_report,
    mock_find_highest_report_level,
    mock_run_convert2rhel,
    mock_inhibitor_check,
    mock_install_convert2rhel,
    mock_setup_convert2rhel,
    mock_update_insights_inventory,
    mock_gather_json_report,
):
    main()

    assert mock_setup_convert2rhel.call_count == 1
    assert mock_install_convert2rhel.call_count == 1
    assert mock_inhibitor_check.call_count == 1
    assert mock_run_convert2rhel.call_count == 1
    assert mock_update_insights_inventory.call_count == 1
    assert mock_gather_json_report.call_count == 1
    assert mock_find_highest_report_level.call_count == 1
    assert mock_gather_textual_report.call_count == 1
    assert mock_generate_report_message.call_count == 1
    # NOTE: we should expect below one call once we don't require rpm because of insights conversion statistics
    assert mock_cleanup_pkg_call.call_count == 0
    # NOTE: successful conversion keeps gpg and repo on system (the backup is also kept)
    assert mock_cleanup_file_exists_call.call_count == 0
    assert mock_cleanup_file_restore_call.call_count == 0
    assert mock_transform_raw_data.call_count == 1
    assert mock_get_system_distro_version.call_count == 1
    assert mock_is_non_eligible_releases.call_count == 1


# fmt: off
@patch("scripts.conversion_script.gather_json_report", side_effect=[{"actions": []}])
@patch("scripts.conversion_script.update_insights_inventory", side_effect=Mock())
@patch("scripts.conversion_script.setup_convert2rhel", side_effect=Mock())
@patch("scripts.conversion_script.check_convert2rhel_inhibitors_before_run", return_value=("", 0))
@patch("scripts.conversion_script.install_convert2rhel", return_value=(True, 1))
@patch("scripts.conversion_script.run_convert2rhel", side_effect=Mock())
@patch("scripts.conversion_script.find_highest_report_level", side_effect=Mock(return_value=["SUCCESS"]))
@patch("scripts.conversion_script.gather_textual_report", side_effect=Mock(return_value=""))
@patch("scripts.conversion_script.generate_report_message", side_effect=Mock(return_value=("inhibited", False)))
@patch("scripts.conversion_script.transform_raw_data", side_effect=Mock(return_value=""))
# These patches are calls made in cleanup
@patch("os.path.exists", return_value=False)
@patch("scripts.conversion_script._create_or_restore_backup_file", side_effect=Mock())
@patch("scripts.conversion_script.run_subprocess", return_value=("", 1))
@patch("scripts.conversion_script.get_system_distro_version", return_value=("centos", "7"))
@patch("scripts.conversion_script.is_non_eligible_releases", return_value=False)
# fmt: on
def test_main_inhibited_c2r_installed(
    mock_is_non_eligible_releases,
    mock_get_system_distro_version,
    mock_cleanup_pkg_call,
    mock_cleanup_file_restore_call,
    mock_cleanup_file_exists_call,
    mock_transform_raw_data,
    mock_generate_report_message,
    mock_gather_textual_report,
    mock_find_highest_report_level,
    mock_run_convert2rhel,
    mock_inhibitor_check,
    mock_install_convert2rhel,
    mock_setup_convert2rhel,
    mock_update_insights_inventory,
    mock_gather_json_report,
):
    main()

    assert mock_setup_convert2rhel.call_count == 1
    assert mock_install_convert2rhel.call_count == 1
    assert mock_inhibitor_check.call_count == 1
    assert mock_run_convert2rhel.call_count == 1
    assert mock_update_insights_inventory.call_count == 1
    assert mock_gather_json_report.call_count == 1
    assert mock_find_highest_report_level.call_count == 1
    assert mock_gather_textual_report.call_count == 1
    assert mock_generate_report_message.call_count == 1
    assert mock_cleanup_pkg_call.call_count == 1
    assert mock_cleanup_file_exists_call.call_count == 2
    assert mock_cleanup_file_restore_call.call_count == 2
    assert mock_transform_raw_data.call_count == 1
    assert mock_get_system_distro_version.call_count == 1
    assert mock_is_non_eligible_releases.call_count == 1


# fmt: off
@patch("__builtin__.open", new_callable=mock_open())
@patch("scripts.conversion_script.gather_json_report", side_effect=[{"actions": []}])
@patch("scripts.conversion_script.setup_convert2rhel", side_effect=Mock())
@patch("scripts.conversion_script.install_convert2rhel", return_value=(False, 1))
@patch("scripts.conversion_script.check_convert2rhel_inhibitors_before_run", return_value=("", 0))
@patch("scripts.conversion_script.run_convert2rhel", side_effect=ProcessError("test", "Process error"))
@patch("scripts.conversion_script.find_highest_report_level", side_effect=Mock(return_value=["SUCCESS"]))
@patch("scripts.conversion_script.gather_textual_report", side_effect=Mock(return_value=""))
@patch("scripts.conversion_script.generate_report_message", side_effect=Mock(return_value=("failed", False)))
@patch("scripts.conversion_script.cleanup", side_effect=Mock())
@patch("scripts.conversion_script.get_system_distro_version", return_value=("centos", "7"))
@patch("scripts.conversion_script.is_non_eligible_releases", return_value=False)
# fmt: on
def test_main_process_error(
    mock_is_non_eligible_releases,
    mock_get_system_distro_version,
    mock_cleanup,
    mock_generate_report_message,
    mock_gather_textual_report,
    mock_find_highest_report_level,
    mock_run_convert2rhel,
    mock_inhibitor_check,
    mock_install_convert2rhel,
    mock_setup_convert2rhel,
    mock_gather_json_report,
    mock_open_func,
):
    main()

    assert mock_setup_convert2rhel.call_count == 1
    assert mock_install_convert2rhel.call_count == 1
    assert mock_inhibitor_check.call_count == 1
    assert mock_run_convert2rhel.call_count == 1
    assert mock_gather_json_report.call_count == 0
    assert mock_find_highest_report_level.call_count == 0
    assert mock_gather_textual_report.call_count == 0
    assert mock_generate_report_message.call_count == 0
    assert mock_cleanup.call_count == 1
    assert mock_open_func.call_count == 0
    assert mock_get_system_distro_version.call_count == 1
    assert mock_is_non_eligible_releases.call_count == 1


# fmt: off
@patch("__builtin__.open", new_callable=mock_open(read_data="not json serializable"))
@patch("scripts.conversion_script.setup_convert2rhel", side_effect=Mock())
@patch("scripts.conversion_script.install_convert2rhel", return_value=(False, 1))
@patch("scripts.conversion_script.check_convert2rhel_inhibitors_before_run", return_value=("", 0))
@patch("scripts.conversion_script.run_convert2rhel", side_effect=Mock())
@patch("scripts.conversion_script.find_highest_report_level", side_effect=Mock(return_value=["SUCCESS"]))
@patch("scripts.conversion_script.gather_textual_report", side_effect=Mock(return_value="failed"))
@patch("scripts.conversion_script.generate_report_message", side_effect=Mock(return_value=("", False)))
@patch("scripts.conversion_script.cleanup", side_effect=Mock())
@patch("scripts.conversion_script.get_system_distro_version", return_value=("centos", "7"))
@patch("scripts.conversion_script.is_non_eligible_releases", return_value=False)
# fmt: on
def test_main_general_exception(
    mock_is_non_eligible_releases,
    mock_get_system_distro_version,
    mock_cleanup,
    mock_generate_report_message,
    mock_gather_textual_report,
    mock_find_highest_report_level,
    mock_run_convert2rhel,
    mock_inhibitor_check,
    mock_install_convert2rhel,
    mock_setup_convert2rhel,
    mock_open_func,
):
    main()

    assert mock_open_func.call_count == 1
    assert mock_setup_convert2rhel.call_count == 1
    assert mock_install_convert2rhel.call_count == 1
    assert mock_inhibitor_check.call_count == 1
    assert mock_run_convert2rhel.call_count == 1
    assert mock_find_highest_report_level.call_count == 0
    assert mock_gather_textual_report.call_count == 0
    assert mock_generate_report_message.call_count == 0
    assert mock_cleanup.call_count == 1
    assert mock_get_system_distro_version.call_count == 1
    assert mock_is_non_eligible_releases.call_count == 1


# fmt: off
@patch("__builtin__.open", new_callable=mock_open(read_data="not json serializable"))
@patch("scripts.conversion_script.setup_convert2rhel", side_effect=Mock())
@patch("scripts.conversion_script.install_convert2rhel", side_effect=Mock())
@patch("os.path.exists", return_value=False)
@patch("scripts.conversion_script._check_ini_file_modified", return_value=True)
@patch("scripts.conversion_script.run_convert2rhel", side_effect=Mock())
@patch("scripts.conversion_script.find_highest_report_level", side_effect=Mock(return_value=["SUCCESS"]))
@patch("scripts.conversion_script.gather_textual_report", side_effect=Mock(return_value=""))
@patch("scripts.conversion_script.generate_report_message", side_effect=Mock(return_value=("", False)))
@patch("scripts.conversion_script.cleanup", side_effect=Mock())
@patch("scripts.conversion_script.get_system_distro_version", return_value=("centos", "7"))
@patch("scripts.conversion_script.is_non_eligible_releases", return_value=False)
# fmt: on
def test_main_inhibited_ini_modified(
    mock_is_non_eligible_releases,
    mock_get_system_distro_version,
    mock_cleanup,
    mock_generate_report_message,
    mock_gather_textual_report,
    mock_find_highest_report_level,
    mock_run_convert2rhel,
    mock_custom_ini,
    mock_ini_modified,
    mock_install_convert2rhel,
    mock_setup_convert2rhel,
    mock_open_func,
):
    main()

    assert mock_open_func.call_count == 0
    assert mock_setup_convert2rhel.call_count == 1
    assert mock_install_convert2rhel.call_count == 0
    assert mock_custom_ini.call_count == 1
    assert mock_ini_modified.call_count == 1
    assert mock_run_convert2rhel.call_count == 0
    assert mock_find_highest_report_level.call_count == 0
    assert mock_gather_textual_report.call_count == 0
    assert mock_generate_report_message.call_count == 0
    assert mock_cleanup.call_count == 1
    assert mock_get_system_distro_version.call_count == 1
    assert mock_is_non_eligible_releases.call_count == 1


# fmt: off
@patch("__builtin__.open", new_callable=mock_open(read_data="not json serializable"))
@patch("scripts.conversion_script.setup_convert2rhel", side_effect=Mock())
@patch("scripts.conversion_script.install_convert2rhel", side_effect=Mock())
@patch("os.path.exists", return_value=True)
@patch("scripts.conversion_script.run_convert2rhel", side_effect=Mock())
@patch("scripts.conversion_script.find_highest_report_level", side_effect=Mock(return_value=["SUCCESS"]))
@patch("scripts.conversion_script.gather_textual_report", side_effect=Mock(return_value=""))
@patch("scripts.conversion_script.generate_report_message", side_effect=Mock(return_value=("", False)))
@patch("scripts.conversion_script.cleanup", side_effect=Mock())
@patch("scripts.conversion_script.get_system_distro_version", return_value=("centos", "7"))
@patch("scripts.conversion_script.is_non_eligible_releases", return_value=False)
# fmt: on
def test_main_inhibited_custom_ini(
    mock_is_non_eligible_releases,
    mock_get_system_distro_version,
    mock_cleanup,
    mock_generate_report_message,
    mock_gather_textual_report,
    mock_find_highest_report_level,
    mock_run_convert2rhel,
    mock_inhibitor_check,
    mock_install_convert2rhel,
    mock_setup_convert2rhel,
    mock_open_func,
):
    main()

    assert mock_open_func.call_count == 0
    assert mock_setup_convert2rhel.call_count == 1
    assert mock_inhibitor_check.call_count == 1
    assert mock_install_convert2rhel.call_count == 0
    assert mock_run_convert2rhel.call_count == 0
    assert mock_find_highest_report_level.call_count == 0
    assert mock_gather_textual_report.call_count == 0
    assert mock_generate_report_message.call_count == 0
    assert mock_cleanup.call_count == 1
    assert mock_get_system_distro_version.call_count == 1
    assert mock_is_non_eligible_releases.call_count == 1
