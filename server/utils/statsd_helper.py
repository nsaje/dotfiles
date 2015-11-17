import functools
import time

from contextlib import contextmanager

from statsd.defaults.django import statsd
from django.conf import settings


def get_source():
    return 'one-%s' % settings.HOSTNAME.replace('.', '')


@contextmanager
def statsd_block_timer(path, name):
    start = time.time()
    yield
    new_name = '{0}.{1}.{2}'.format(get_source(), path, name)
    statsd.timing(new_name, int((time.time() - start) * 1000))


def statsd_timer(path, name=None):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with statsd_block_timer(path, name or func.__name__):
                result = func(*args, **kwargs)
            return result
        return wrapper
    return decorator


def statsd_incr(name, count=1):
    statsd.incr('{0}.{1}'.format(get_source(), name), count)


def statsd_gauge(name, value):
    statsd.gauge('{0}.{1}'.format(get_source(), name), value)
