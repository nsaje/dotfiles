import functools
import time

from contextlib import contextmanager

import statsd
from django.conf import settings

_telegraf_client = statsd.StatsClient(settings.TELEGRAF_HOST, settings.TELEGRAF_PORT)


def _get_source():
    return settings.HOSTNAME.replace('.', '-')


def _get_default_tags():
    return {
        'host': _get_source(),
    }


def _get_tags(custom_tags):
    tags = custom_tags.items() + _get_default_tags().items()

    return ','.join('{0}={1}'.format(k, v) for k, v in tags)


@contextmanager
def block_timer(name, **tags):
    start = time.time()
    yield
    new_name = '{name},{tags}'.format(source=_get_source(), name=name, tags=_get_tags(tags))
    _telegraf_client.timing(new_name, int((time.time() - start) * 1000))


def timer(name, **tags):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with block_timer(name, **tags):
                result = func(*args, **kwargs)
            return result
        return wrapper
    return decorator


def incr(name, count, **tags):
    _telegraf_client.incr('{name},{tags}'.format(name=name, tags=_get_tags(tags)), count)


def gauge(name, value, **tags):
    _telegraf_client.gauge('{name},{tags}'.format(name=name, tags=_get_tags(tags)), value)
