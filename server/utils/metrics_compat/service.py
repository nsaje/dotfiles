import time
from contextlib import contextmanager

import decorator

from utils import zlogging

from . import prometheus

logger = zlogging.getLogger(__name__)


def gauge(name, value, **tags):
    try:
        prometheus.gauge(name, value, **tags)
    except Exception:
        logger.exception("Prometheus exception")


def incr(name, count, **tags):
    try:
        prometheus.incr(name, count, **tags)
    except Exception:
        logger.exception("Prometheus exception")


def timing(name, seconds, **tags):
    try:
        prometheus.timing(name, seconds, **tags)
    except Exception:
        logger.exception("Prometheus exception")


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
