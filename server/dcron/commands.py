import shlex

from django.conf import settings
from django.core import management

from dcron import exceptions


def extract_management_command_name(command: str) -> str:  # typing (for mypy check)
    """
    Extract the name of management command.
    :param command: the command
    :return: the name of management command
    """

    if command is None:
        raise exceptions.ParameterException("Command can not be None")

    input_arguments = shlex.split(command)

    if len(input_arguments) <= 1:
        raise exceptions.ParameterException("Command needs at least two arguments")

    if input_arguments[0] != settings.DCRON["base_command"]:
        raise exceptions.ParameterException("Illegal base command: %s" % input_arguments[0])

    return input_arguments[1]


def extract_and_verify_management_command_name(command: str) -> str:  # typing (for mypy check)
    """
    Extract and verify the name of management command.
    It checks if the management command is registered and that it is and instance of DCronCommand.
    :param command: the command
    :return: the name of management command
    """

    command_name = extract_management_command_name(command)

    if command_name not in management.get_commands():
        raise exceptions.UnregisteredManagementCommand("%s is not a registered management command" % command_name)

    # TODO check that command_name is an instance of DCronCommand

    return command_name
