import functools
import time

from statsd.defaults.django import statsd
from django.conf import settings


def get_source():
    return 'one-%s' % settings.HOSTNAME.replace('.', '')


def statsd_timer(path, name=None):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start = time.time()
            result = func(*args, **kwargs)
            new_name = '{0}.{1}.{2}'.format(get_source(), path, name or func.__name__)
            statsd.timing(new_name, int((time.time() - start) * 1000))

            return result
        return wrapper
    return decorator


def statsd_incr(name):
    statsd.incr('{0}.{1}'.format(get_source(), name))


def statsd_gauge(name, value):
    statsd.gauge('{0}.{1}'.format(get_source(), name), value)
