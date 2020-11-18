from concurrent.futures import ThreadPoolExecutor
from functools import wraps
from threading import Thread

from django.conf import settings
from django.db import connection

import utils.request_context
from utils import zlogging

logger = zlogging.getLogger(__name__)

TRANSACTION_END_WAIT = 3


"""
Both classes implement the same API. Whenever you want to replace async execution with
in-sync execution just uncomment the last line of this module.

This is useful when debugging or investigating performance problems (django debug toolbar won't
record SQL statements executed in other than main thread).
"""


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


class RealAsyncFunction(Thread):
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

    def __init__(self, func, log_exception=True):
        super(AsyncFunction, self).__init__()
        self.func = func
        self._result = None
        self._exception = None
        self._request_context = utils.request_context.get_dict()
        self._log_exception = log_exception

    def get_result(self):
        if self._exception:
            raise self._exception
        return self._result

    def run(self):
        # make sure the async thread has the correct request context
        utils.request_context.set_dict(self._request_context)
        try:
            self._result = self.func()
        except Exception as e:
            self._exception = e
            if self._log_exception:
                logger.exception(e)
        finally:
            connection.close()

    def join_and_get_result(self, timeout=None):
        self.join(timeout)
        return self.get_result()


AsyncFunction = RealAsyncFunction
if settings.ENABLE_SILK:
    AsyncFunction = MockAsyncFunction

# uncomment the following statement to disable async behaviour
# AsyncFunction = MockAsyncFunction


class DjangoConnectionThreadPoolExecutor(ThreadPoolExecutor):
    """
    Taken from:
    https://stackoverflow.com/questions/57211476/django-orm-leaks-connections-when-using-threadpoolexecutor
    When a function is passed into the ThreadPoolExecutor via either submit() or map(),
    this will wrap the function, and make sure that close_django_db_connection() is called
    inside the thread when it's finished so Django doesn't leak DB connections.

    Since map() calls submit(), only submit() needs to be overwritten.
    """

    def submit(*args, **kwargs):
        """
        It takes the args filtering/unpacking logic from

        https://github.com/python/cpython/blob/3.7/Lib/concurrent/futures/thread.py

        so that it can properly get the function object the same way it was done there.
        """
        if len(args) >= 2:
            self, fn, *args = args
            fn = self.generate_thread_closing_wrapper(fn=fn)
        elif not args:
            raise TypeError("descriptor 'submit' of 'ThreadPoolExecutor' object " "needs an argument")
        elif "fn" in kwargs:
            fn = self.generate_thread_closing_wrapper(fn=kwargs.pop("fn"))
            self, *args = args

        return super(self.__class__, self).submit(fn, *args, **kwargs)

    def generate_thread_closing_wrapper(self, fn):
        @wraps(fn)
        def new_func(*args, **kwargs):
            try:
                res = fn(*args, **kwargs)
            except Exception as e:
                self.close_django_db_connection()
                raise e
            else:
                self.close_django_db_connection()
                return res

        return new_func

    def close_django_db_connection(self):
        connection.close()
