import time
from contextlib import contextmanager

import decorator
import influx

import structlog

from . import prometheus

logger = structlog.get_logger(__name__)


def gauge(name, value, **tags):
    try:
        influx.gauge(name, value, **tags)
    finally:
        try:
            prometheus.gauge(name, value, **tags)
        except Exception:
            logger.exception("Prometheus exception")


def incr(name, count, **tags):
    try:
        influx.incr(name, count, **tags)
    finally:
        try:
            prometheus.incr(name, count, **tags)
        except Exception:
            logger.exception("Prometheus exception")


def timing(name, seconds, **tags):
    try:
        influx.timing(name, seconds, **tags)
    finally:
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
