from unittest import TestCase

from utils.timeout_decorator import timeout_decorator

TIMEOUT_SECONDS = 900
EXCEPTION_MESSAGE = f"Exceeded APT test limit of {TIMEOUT_SECONDS} seconds."


class TimeoutMeta(type):
    """
    A metaclass is used here to make sure that every test method of every subclass is decorated and thus that the
    timeouts for the whole APT test suite are enforced.
    """

    def __new__(cls, name, bases, attr_dict):
        for key, attr in attr_dict.items():
            if callable(attr) and key.startswith("test_"):
                attr_dict[key] = timeout_decorator(TIMEOUT_SECONDS, exception_message=EXCEPTION_MESSAGE)(attr)
        return type.__new__(cls, name, bases, attr_dict)


class APTTestCase(TestCase, metaclass=TimeoutMeta):
    pass
