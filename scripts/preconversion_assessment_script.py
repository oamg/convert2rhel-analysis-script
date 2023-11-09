import hashlib
import json
import os
import subprocess
import copy

from urllib2 import urlopen

STATUS_CODE = {
    "SUCCESS": 0,
    "INFO": 25,
    "WARNING": 51,
    "SKIP": 101,
    "OVERRIDABLE": 152,
    "ERROR": 202,
}
# Revert the `STATUS_CODE` dictionary to map number: name instead of name:
# number as used originally.
STATUS_CODE_NAME = {number: name for name, number in STATUS_CODE.items()}
# Path to the convert2rhel report json file.
C2R_REPORT_FILE = "/var/log/convert2rhel/convert2rhel-pre-conversion.json"
# Path to the convert2rhel report textual file.
C2R_REPORT_TXT_FILE = "/var/log/convert2rhel/convert2rhel-pre-conversion.txt"


class RequiredFile(object):
    """Holds data about files needed to download convert2rhel"""

    def __init__(self, path="", host=""):
        self.path = path
        self.host = host
        self.sha512_on_system = None
        self.is_file_present = False


class ProcessError(Exception):
    """Custom exception to report errors during setup and run of conver2rhel"""

    def __init__(self, message, report):
        super(ProcessError, self).__init__(report)
        self.message = message
        self.report = report


class OutputCollector(object):
    """Wrapper class for script expected stdout"""

    # pylint: disable=too-many-instance-attributes
    # pylint: disable=too-many-arguments
    # Eight and five is reasonable in this case.

    def __init__(self, status="", message="", report="", entries=None, alert=False):
        self.status = status
        self.alert = alert
        self.message = message
        self.report = report
        self.tasks_format_version = "1.0"
        self.tasks_format_id = "oamg-format"
        self.entries = entries
        self.report_json = None

    def to_dict(self):
        # If we have entries, then we change report_json to be a dictionary
        # with the needed values, otherwise, we leave it as `None` to be
        # transformed to `null` in json.
        if self.entries:
            self.report_json = {
                "tasks_format_version": self.tasks_format_version,
                "tasks_format_id": self.tasks_format_id,
                "entries": self.entries,
            }

        return {
            "status": self.status,
            "alert": self.alert,
            "message": self.message,
            "report": self.report,
            "report_json": self.report_json,
        }


def find_highest_report_level(actions):
    """
    Gather status codes from messages and result. We are not seeking for
    differences between them as we want all the results, no matter from where
    they come.
    """
    print("Collecting and combining report status.")
    action_level_combined = []
    for value in actions.values():
        action_level_combined.append(value["result"]["level"])
        for message in value["messages"]:
            action_level_combined.append(message["level"])

    valid_action_levels = [
        level for level in action_level_combined if level in STATUS_CODE
    ]
    valid_action_levels.sort(key=lambda status: STATUS_CODE[status], reverse=True)
    return valid_action_levels[0]


def gather_json_report():
    """Collect the json report generated by convert2rhel."""
    print("Collecting JSON report.")
    with open(C2R_REPORT_FILE, "r") as handler:
        data = json.load(handler)

    if not data:
        raise ProcessError(
            message="Expected content missing in the pre-conversion analysis report.",
            report="The convert2rhel analysis report file '%s' does not contain any JSON data in it."
            % C2R_REPORT_FILE,
        )

    return data


def gather_textual_report():
    """Collect the textual report generated by convert2rhel."""
    data = ""
    if os.path.exists(C2R_REPORT_TXT_FILE):
        with open(C2R_REPORT_TXT_FILE, mode="r") as handler:
            data = handler.read()
    return data


def generate_report_message(highest_status):
    """Generate a report message based on the status severity."""
    message = ""
    alert = False

    if STATUS_CODE[highest_status] < STATUS_CODE["WARNING"]:
        message = "No problems found. The system is ready for conversion."

    if STATUS_CODE[highest_status] == STATUS_CODE["WARNING"]:
        message = (
            "The conversion can proceed. "
            "However, there is one or more warnings about issues that might occur after the conversion."
        )

    if STATUS_CODE[highest_status] > STATUS_CODE["WARNING"]:
        message = "The conversion cannot proceed. You must resolve existing issues to perform the conversion."
        alert = True

    return message, alert


def setup_convert2rhel(required_files):
    """Setup convert2rhel tool by downloading the required files."""
    print("Downloading required files.")
    for required_file in required_files:
        response = urlopen(required_file.host)
        data = response.read()
        downloaded_file_sha512 = hashlib.sha512(data)

        if os.path.exists(required_file.path):
            print(
                "File '%s' is already present on the system. Downloading a copy in order to check if they are the same."
                % required_file.path
            )
            if (
                downloaded_file_sha512.hexdigest()
                != required_file.sha512_on_system.hexdigest()
            ):
                raise ProcessError(
                    message="Hash mismatch between the downloaded file and the one present on the system.",
                    report="File '%s' present on the system does not match the one downloaded. Stopping the execution."
                    % required_file.path,
                )
        else:
            directory = os.path.dirname(required_file.path)
            if not os.path.exists(directory):
                print("Creating directory at '%s'" % directory)
                os.makedirs(directory, mode=0o755)

            print("Writing file to destination: '%s'" % required_file.path)
            with open(required_file.path, mode="w") as handler:
                handler.write(data)
                os.chmod(required_file.path, 0o644)


# Code taken from
# https://github.com/oamg/convert2rhel/blob/v1.4.1/convert2rhel/utils.py#L345
# and modified to adapt the needs of the tools that are being executed in this
# script.
def run_subprocess(cmd, print_cmd=True, env=None):
    """
    Call the passed command and optionally log the called command
    (print_cmd=True) and environment variables in form of dictionary(env=None).
    Switching off printing the command can be useful in case it contains a
    password in plain text.

    The cmd is specified as a list starting with the command and followed by a
    list of arguments. Example: ["yum", "install", "<package>"]
    """
    # This check is here because we passed in strings in the past and changed
    # to a list for security hardening.  Remove this once everyone is
    # comfortable with using a list instead.
    if isinstance(cmd, str):
        raise TypeError("cmd should be a list, not a str")

    if print_cmd:
        print("Calling command '%s'" % " ".join(cmd))

    process = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=1, env=env
    )
    output = ""
    for line in iter(process.stdout.readline, b""):
        line = line.decode("utf8")
        output += line

    # Call wait() to wait for the process to terminate so that we can
    # get the return code.
    process.wait()

    return output, process.returncode


def install_convert2rhel():
    """Install the convert2rhel tool to the system."""
    print("Installing & updating Convert2RHEL package.")
    output, returncode = run_subprocess(
        ["yum", "install", "convert2rhel", "-y"],
    )
    if returncode:
        raise ProcessError(
            message="Failed to install convert2rhel RPM.",
            report="Installing convert2rhel with yum exited with code '%s' and output: %s."
            % (returncode, output.rstrip("\n")),
        )

    output, returncode = run_subprocess(["yum", "update", "convert2rhel", "-y"])
    if returncode:
        raise ProcessError(
            message="Failed to update convert2rhel RPM.",
            report="Updating convert2rhel with yum exited with code '%s' and output: %s."
            % (returncode, output.rstrip("\n")),
        )


def run_convert2rhel():
    """
    Run the convert2rhel tool assigning the correct environment variables.
    """
    print("Running Convert2RHEL Analysis")
    env = {"PATH": os.environ["PATH"]}

    if "RHC_WORKER_CONVERT2RHEL_DISABLE_TELEMETRY" in os.environ:
        env["CONVERT2RHEL_DISABLE_TELEMETRY"] = os.environ[
            "RHC_WORKER_CONVERT2RHEL_DISABLE_TELEMETRY"
        ]

    _, returncode = run_subprocess(["/usr/bin/convert2rhel", "analyze", "-y"], env=env)
    if returncode:
        raise ProcessError(
            message=(
                "An error occurred during the pre-conversion analysis. "
                "For details, refer to the convert2rhel log file on the host at /var/log/convert2rhel/convert2rhel.log"
            ),
            report="convert2rhel execution exited with code '%s'." % returncode,
        )


def cleanup(required_files):
    """
    Cleanup the downloaded files downloaded in previous steps in this script.

    If any of the required files was already present on the system, the script
    will not remove that file, as it understand that it is a system file and
    not something that was downloaded by the script.
    """
    for required_file in required_files:
        if not required_file.is_file_present and os.path.exists(required_file.path):
            print(
                "Removing the file '%s' as it was previously downloaded."
                % required_file.path
            )
            os.remove(required_file.path)
            continue

        print(
            "File '%s' was present on the system before the execution. Skipping the removal."
            % required_file.path
        )


def verify_required_files_are_present(required_files):
    """Verify if the required files are already present on the system."""
    print("Checking if required files are present on the system.")
    for required_file in required_files:
        # Avoid race conditions
        try:
            print("Checking for file %s" % required_file.path)
            with open(required_file.path, mode="r") as handler:
                required_file.sha512_on_system = hashlib.sha512(handler.read())
                required_file.is_file_present = True
        except (IOError, OSError):
            required_file.is_file_present = False


def _generate_message_key(message, action_id):
    """
    Helper method to generate a key field in the message composed by action_id
    and message_id.
    Returns modified copy of original message.
    """
    new_message = copy.deepcopy(message)

    new_message["key"] = "%s::%s" % (action_id, message["id"])
    del new_message["id"]

    return new_message


def _generate_detail_block(message):
    """
    Helper method to generate the detail key that is composed by the
    remediations and diagnosis fields.
    Returns modified copy of original message.
    """
    new_message = copy.deepcopy(message)
    detail_block = {
        "remediations": [],
        "diagnosis": [],
    }

    remediation_key = "remediations" if "remediations" in new_message else "remediation"
    detail_block["remediations"].append(
        {"context": new_message.pop(remediation_key, "")}
    )
    detail_block["diagnosis"].append({"context": new_message.pop("diagnosis", "")})
    new_message["detail"] = detail_block
    return new_message


def _rename_dictionary_key(message, new_key, old_key):
    """Helper method to rename keys in a flatten dictionary."""
    new_message = copy.deepcopy(message)
    new_message[new_key] = new_message.pop(old_key)
    return new_message


def _filter_message_level(message, level):
    """
    Filter for messages with specific level. If any of the message matches the
    level, return None, otherwise, if it is different from what is expected,
    return the message received to continue with the other transformations.
    """
    if message["level"] != level:
        return message

    return {}


def apply_message_transform(message, action_id):
    """Apply the necessary data transformation to the given messages."""
    if not _filter_message_level(message, level="SUCCESS"):
        return {}

    new_message = _generate_message_key(message, action_id)
    new_message = _rename_dictionary_key(new_message, "severity", "level")
    new_message = _rename_dictionary_key(new_message, "summary", "description")
    new_message = _generate_detail_block(new_message)

    # Appending the `modifiers` key to the message here for now. Once we have
    # this feature in the frontend, we can populate the data with it.
    new_message["modifiers"] = []

    return new_message


def transform_raw_data(raw_data):
    """
    Method that will transform the raw data given and output in the expected
    format.

    The expected format will be a flattened version of both results and
    messages into a single
    """
    new_data = []
    for action_id, result in raw_data["actions"].items():
        # Format the results as a single list
        for message in result["messages"]:
            new_data.append(apply_message_transform(message, action_id))

        new_data.append(apply_message_transform(result["result"], action_id))

    # Filter out None values before returning
    return [data for data in new_data if data]


def main():
    """Main entrypoint for the script."""
    output = OutputCollector()
    required_files = [
        RequiredFile(
            path="/etc/pki/rpm-gpg/RPM-GPG-KEY-redhat-release",
            host="https://www.redhat.com/security/data/fd431d51.txt",
        ),
        RequiredFile(
            path="/etc/yum.repos.d/convert2rhel.repo",
            host="https://ftp.redhat.com/redhat/convert2rhel/7/convert2rhel.repo",
        ),
    ]

    try:
        # Setup Convert2RHEL to be executed.
        verify_required_files_are_present(required_files)
        setup_convert2rhel(required_files)
        install_convert2rhel()
        run_convert2rhel()

        # Gather JSON & Textual report
        data = gather_json_report()
        output.report = gather_textual_report()

        highest_level = find_highest_report_level(actions=data["actions"])
        # Set the first position of the list as being the final status, that's
        # needed because `find_highest_report_level` will sort out the list
        # with the highest priority first.
        output.status = highest_level

        # Generate report message and transform the raw data into entries for
        # Insights.
        message, alert = generate_report_message(highest_level)
        output.message = message
        output.alert = alert
        output.entries = transform_raw_data(data)
        print("Pre-conversion assessment script finish successfully!")
    except ProcessError as exception:
        print(exception.report)
        output = OutputCollector(
            status="ERROR",
            alert=True,
            message=exception.message,
            report=exception.report,
        )
    except Exception as exception:
        print(str(exception))
        output = OutputCollector(
            status="ERROR",
            alert=True,
            message="An unexpected error occurred. Expand the row for more details.",
            report=str(exception),
        )
    finally:
        print("Cleaning up modifications to the system.")
        cleanup(required_files)

        print("### JSON START ###")
        print(json.dumps(output.to_dict(), indent=4))
        print("### JSON END ###")


if __name__ == "__main__":
    main()
