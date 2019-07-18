import time
from contextlib import contextmanager

import decorator
import influx

from . import prometheus


def gauge(name, value, **tags):
    try:
        influx.gauge(name, value, **tags)
    finally:
        prometheus.gauge(name, value, **tags)


def incr(name, count, **tags):
    try:
        influx.incr(name, count, **tags)
    finally:
        prometheus.incr(name, count, **tags)


def timing(name, seconds, **tags):
    try:
        influx.timing(name, seconds, **tags)
    finally:
        prometheus.timing(name, seconds, **tags)


@contextmanager
def block_timer(name, **tags):
    start = time.time()
    yield
    timing(name, (time.time() - start), **tags)


def timer(name, **tags):
    def decorate(func):
        def wrapper(func, *args, **kwargs):
            with block_timer(name, **tags):
                result = func(*args, **kwargs)
            return result

        return decorator.decorate(func, wrapper)

    return decorate
