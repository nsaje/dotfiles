import functools
import time

from statsd.defaults.django import statsd


def statsd_timer(name):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start = time.time()
            result = func(*args, **kwargs)

            new_name = '{0}.{1}'.format(name, func.__name__)
            statsd.timing(new_name, int((time.time() - start) * 1000))

            return result
        return wrapper
    return decorator
