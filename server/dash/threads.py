from threading import Thread
import logging

from django.db import connection

logger = logging.getLogger(__name__)

TRANSACTION_END_WAIT = 3


class MockAsyncFunction(object):
    """
    When running tests use this mock as otherwise we dont have access to data
    that is not in transaction where data from fixtures is.
    """

    def __init__(self, func):
        self.func = func
        self._result = None

    def get_result(self):
        return self._result

    def start(self):
        self._result = self.func()

    def join(self):
        pass

    def join_and_get_result(self):
        self.join()
        return self._result


class AsyncFunction(Thread):
    """
    A more general class that takes a function and runs it in a new thread.
    The recepie:

    some_func = partial(your_function, *your_function_args, **your_function_kwargs)
    thread = AsyncQuery(some_func)
    thread.start()

    # do something else

    # when results are needed do
    thread.join()
    results = thread.result
    """

    def __init__(self, func):
        super(AsyncFunction, self).__init__()
        self.func = func
        self._result = None
        self._exception = None

    def get_result(self):
        if self._exception:
            raise self._exception
        return self._result

    def run(self):
        try:
            self._result = self.func()
        except Exception as e:
            self._exception = e
            logger.exception(e)
        finally:
            connection.close()

    def join_and_get_result(self):
        self.join()
        return self.get_result()
