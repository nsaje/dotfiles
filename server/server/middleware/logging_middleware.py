import time

import ipware.ip

import utils.request_context
from utils import zlogging

from . import common

logger = zlogging.getLogger("zem.request")


def zem_logging_middleware(get_response):
    def middleware(request):
        t0 = time.time()
        response = get_response(request)
        params = dict(
            trace_id=utils.request_context.get("trace_id"),
            request_time_seconds=time.time() - t0,
            ip=ipware.ip.get_ip(request),
        )
        params.update(common.extract_request_params(request))
        params.update(common.extract_response_params(response))
        logger.info("HTTP Access", **params)
        return response

    return middleware
