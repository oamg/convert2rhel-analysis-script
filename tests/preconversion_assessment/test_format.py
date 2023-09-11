from pprint import pprint
import pytest

from scripts.preconversion_assessment_script import (
    _generate_message_key,
    _generate_detail_block,
    _rename_dictionary_key,
    apply_message_transform,
    transform_raw_data,
)


@pytest.mark.parametrize(
    ("data", "action_id", "expected"),
    (
        ({"id": "test"}, "ANOTHER_TEST", {"key": "ANOTHER_TEST::test"}),
        (
            {"id": "test", "random-key": "random-value"},
            "A_TEST",
            {"key": "A_TEST::test", "random-key": "random-value"},
        ),
    ),
)
def test_generate_message_key(data, action_id, expected):
    result = _generate_message_key(data, action_id)

    assert result == expected
    assert not "id" in result


@pytest.mark.parametrize(
    ("data", "expected"),
    (
        (
            {"remediation": "test", "diagnosis": "test"},
            {
                "detail": {
                    "remediation": {"context": "test"},
                    "diagnosis": {"context": "test"},
                }
            },
        ),
        (
            {"remediation": "test", "diagnosis": "test", "test-key": "test-value"},
            {
                "detail": {
                    "remediation": {"context": "test"},
                    "diagnosis": {"context": "test"},
                },
                "test-key": "test-value",
            },
        ),
    ),
)
def test_generate_detail_block(data, expected):
    result = _generate_detail_block(data)

    assert result == expected
    assert not "remediation" in expected
    assert not "diagnosis" in expected


@pytest.mark.parametrize(
    ("data", "new_key", "old_key", "expected"),
    (
        ({"a-key": "a-value"}, "AKey", "a-key", {"AKey": "a-value"}),
        ({"a-key": "a-value"}, "a  key", "a-key", {"a  key": "a-value"}),
    ),
)
def test_rename_dictionary_key(data, new_key, old_key, expected):
    result = _rename_dictionary_key(data, new_key, old_key)

    assert result == expected
    assert not old_key in result


@pytest.mark.parametrize(
    ("data", "action_id", "expected"),
    (
        (
            {
                "id": "ultra",
                "remediation": "test",
                "diagnosis": "test",
                "level": "WARNING",
                "description": "test",
            },
            "test",
            {
                "key": "test::ultra",
                "detail": {
                    "remediation": {"context": "test"},
                    "diagnosis": {"context": "test"},
                },
                "severity": "WARNING",
                "summary": "test",
                "modifiers": [],
            },
        ),
    ),
)
def test_apply_message_transform(data, action_id, expected):
    result = apply_message_transform(data, action_id)

    assert result == expected
    # All transformations that are done now
    assert not "remediation" in result
    assert not "diagnosis" in result
    assert not "id" in result
    assert not "level" in result
    assert not "description" in result


@pytest.mark.parametrize(
    ("data", "expected"),
    (
        (
            {
                "actions": {
                    "LIST_THIRD_PARTY_PACKAGES": {
                        "messages": [
                            {
                                "title": "List packages not packaged by the original OS vendor.",
                                "description": "Only packages from the original OS vendor and Red Hat will be converted.  List any other packages so the user knows they won't be converted and can choose whether they think it is safe to proceed.",
                                "diagnosis": "Only packages signed by {{source_distro}} are to be replaced. Red Hat support won't be provided for the following third party packages:\n{% for pkg in third_party_pkgs %}\n* {{pkg}}\n{% endfor %}\n",
                                "id": "THIRD_PARTY_PACKAGES_LIST",
                                "level": "WARNING",
                                "remediation": "You may want to remove those packages before performing the conversion or manually evaluate if those packages are working after the conversion finishes.",
                                "variables": {
                                    "source_distro": "CentOS",
                                    "third_party_pkgs": [
                                        "google-chrome-stable",
                                        "meld",
                                    ],
                                },
                            }
                        ],
                        "result": {
                            "title": "List packages not packaged by the original OS vendor.",
                            "description": "Only packages from the original OS vendor and Red Hat will be converted.  List any other packages so the user knows they won't be converted and can choose whether they think it is safe to proceed.",
                            "diagnosis": "",
                            "id": "SUCCESS",
                            "level": "SUCCESS",
                            "remediation": "",
                            "variables": {},
                        },
                    },
                    "RHEL_COMPATIBLE_KERNEL": {
                        "messages": [],
                        "result": {
                            "title": "Ensure the booted kernel is compatible with RHEL.",
                            "description": "Check that the kernel currently loaded on the host is signed, is standard (not UEK, realtime, etc), and has the same version as in RHEL.  These criteria are designed to check whether the RHEL kernel will provide the same capabilities as the original system.",
                            "diagnosis": "The booted kernel {{ kernel_version }} is compatible with RHEL.",
                            "id": "SUCCESS",
                            "level": "SUCCESS",
                            "remediation": "",
                            "variables": {
                                "kernel_version": "3.10.0-1160.88.1.el7.x86_64"
                            },
                        },
                    },
                }
            },
            [
                {
                    "key": "RHEL_COMPATIBLE_KERNEL::SUCCESS",
                    "title": "Ensure the booted kernel is compatible with RHEL.",
                    "variables": {"kernel_version": "3.10.0-1160.88.1.el7.x86_64"},
                    "detail": {
                        "remediation": {"context": ""},
                        "diagnosis": {
                            "context": "The booted kernel {{ kernel_version }} is compatible with RHEL."
                        },
                    },
                    "summary": "Check that the kernel currently loaded on the host is signed, is standard (not UEK, realtime, etc), and has the same version as in RHEL.  These criteria are designed to check whether the RHEL kernel will provide the same capabilities as the original system.",
                    "severity": "SUCCESS",
                    "modifiers": [],
                },
                {
                    "key": "LIST_THIRD_PARTY_PACKAGES::THIRD_PARTY_PACKAGES_LIST",
                    "title": "List packages not packaged by the original OS vendor.",
                    "variables": {
                        "third_party_pkgs": ["google-chrome-stable", "meld"],
                        "source_distro": "CentOS",
                    },
                    "detail": {
                        "remediation": {
                            "context": "You may want to remove those packages before performing the conversion or manually evaluate if those packages are working after the conversion finishes."
                        },
                        "diagnosis": {
                            "context": "Only packages signed by {{source_distro}} are to be replaced. Red Hat support won't be provided for the following third party packages:\n{% for pkg in third_party_pkgs %}\n* {{pkg}}\n{% endfor %}\n"
                        },
                    },
                    "summary": "Only packages from the original OS vendor and Red Hat will be converted.  List any other packages so the user knows they won't be converted and can choose whether they think it is safe to proceed.",
                    "severity": "WARNING",
                    "modifiers": [],
                },
                {
                    "key": "LIST_THIRD_PARTY_PACKAGES::SUCCESS",
                    "title": "List packages not packaged by the original OS vendor.",
                    "variables": {},
                    "detail": {
                        "remediation": {"context": ""},
                        "diagnosis": {"context": ""},
                    },
                    "summary": "Only packages from the original OS vendor and Red Hat will be converted.  List any other packages so the user knows they won't be converted and can choose whether they think it is safe to proceed.",
                    "severity": "SUCCESS",
                    "modifiers": [],
                },
            ],
        ),
        (
            {
                "actions": {
                    "IS_LOADED_KERNEL_LATEST": {
                        "messages": [],
                        "result": {
                            "title": "Kernel version available in RHEL",
                            "description": "Check whether RHEL contains a kernel of the same or more recent version as the one currently loaded on the host.",
                            "diagnosis": "The version of the loaded kernel is different from the latest version in the enabled system repositories.\n* Latest kernel version available in updates: {{latest_kernel}}\n* Loaded kernel version: {{loaded_kernel}}",
                            "id": "INVALID_KERNEL_VERSION",
                            "level": "ERROR",
                            "remediation": "To proceed with the conversion, update the kernel version by executing the following steps:\n1. yum install {{latest_kernel}} -y\n2. reboot",
                            "variables": {
                                "latest_kernel": "3.10.0-1160.90.1.el7",
                                "loaded_kernel": "3.10.0-1160.88.1.el7",
                            },
                        },
                    }
                }
            },
            [
                {
                    "key": "IS_LOADED_KERNEL_LATEST::INVALID_KERNEL_VERSION",
                    "title": "Kernel version available in RHEL",
                    "variables": {
                        "loaded_kernel": "3.10.0-1160.88.1.el7",
                        "latest_kernel": "3.10.0-1160.90.1.el7",
                    },
                    "detail": {
                        "remediation": {
                            "context": "To proceed with the conversion, update the kernel version by executing the following steps:\n1. yum install {{latest_kernel}} -y\n2. reboot"
                        },
                        "diagnosis": {
                            "context": "The version of the loaded kernel is different from the latest version in the enabled system repositories.\n* Latest kernel version available in updates: {{latest_kernel}}\n* Loaded kernel version: {{loaded_kernel}}"
                        },
                    },
                    "summary": "Check whether RHEL contains a kernel of the same or more recent version as the one currently loaded on the host.",
                    "severity": "ERROR",
                    "modifiers": [],
                }
            ],
        ),
    ),
)
def test_transform_raw_data(data, expected):
    result = transform_raw_data(data)
    print(pprint(result))
    assert result == expected