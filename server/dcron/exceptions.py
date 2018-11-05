class DCronException(Exception):
    """Base Exception in dcron module."""

    pass


class ParameterException(DCronException):
    """Parameter Exeption in dcron module."""

    pass


class UnregisteredManagementCommand(DCronException):
    """Unregistered management command exception."""

    pass
