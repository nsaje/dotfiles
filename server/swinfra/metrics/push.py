import logging
import threading
import time

import prometheus_client

from . import registry

logger = logging.getLogger(__name__)


IN_PUSH_MODE = False
_params = None


def start_push_mode(gateway_addr: str, push_period_seconds: float, job: str = None, push_periodically=True):
    global IN_PUSH_MODE
    global _params

    if IN_PUSH_MODE:
        return

    _params = {"gateway_addr": gateway_addr, "push_period_seconds": push_period_seconds, "job": job}
    registry.set_registry(prometheus_client.CollectorRegistry())
    IN_PUSH_MODE = True

    if not gateway_addr:
        logger.warning("Gateway for push metrics not set up! Prometheus metrics won't be published.")

    if push_periodically and gateway_addr:
        _start_push_thread()


def flush_push_metrics():
    _push_to_gateway()


def _start_push_thread():
    t = threading.Thread(target=_push_to_gateway_periodically)
    t.daemon = True
    t.start()


def _push_to_gateway_periodically():
    push_period_seconds = _params["push_period_seconds"]
    while True:
        next_ts = time.time() + push_period_seconds
        _push_to_gateway()
        time.sleep(max(0, next_ts - time.time()))


def _push_to_gateway():
    gateway_addr = _params["gateway_addr"]
    job = _params["job"]
    try:
        prometheus_client.pushadd_to_gateway(gateway_addr, job=job, registry=registry.get_registry())
    except Exception:
        logger.exception("Exception pushing metrics to Prometheus push gateway")
