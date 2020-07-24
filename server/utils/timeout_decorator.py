"""
Loosely based on https://github.com/pnpnpn/timeout-decorator/blob/master/timeout_decorator/timeout_decorator.py. The
difference is that the approach used here allows for a hard limit to be set for the whole test suite instead of
individual test methods. This is achieved by calculating limit at the time when the decorator is applied instead of when
the function is called.
"""

import functools
import time

from utils import threads


class TimeoutException(AssertionError):
    pass


def timeout_decorator(timeout, exception_message="timeout"):
    def decorate(function):
        limit = time.time() + timeout

        @functools.wraps(function)
        def new_function(*args, **kwargs):
            timeout_wrapper = _TimeoutWrapper(function, limit, exception_message)
            return timeout_wrapper(*args, **kwargs)

        return new_function

    return decorate


class _TimeoutWrapper:
    def __init__(self, function, limit, exception_message):
        self.__function = function
        self.__limit = limit
        self.__exception_message = exception_message

    def __call__(self, *args, **kwargs):
        if time.time() > self.__limit:
            self._raise_timeout_exception()

        t = threads.RealAsyncFunction(functools.partial(self.__function, *args, **kwargs), log_exception=False)
        t.daemon = True
        t.start()

        timeout = self.__limit - time.time()
        result = t.join_and_get_result(timeout)

        if t.is_alive():
            # t.join_and_get_result called with timeout set returns None if timeout was exceeded, so we have to check if
            # the thread is still running
            self._raise_timeout_exception()
        return result

    def _raise_timeout_exception(self):
        raise TimeoutException(self.__exception_message)
