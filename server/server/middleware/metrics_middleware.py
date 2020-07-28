import time

from swinfra import metrics

from . import common

# fmt: off
REQUEST_TIMER = metrics.new_histogram(
    "z1_request_histogram",
    labelnames=("endpoint", "path", "method", "status", "user", "authenticator"),
    buckets=(.005, .01, .025, .05, .075, .1, .25, .5, .75, 1.0, 2.5, 5.0, 7.5, 10.0, 20.0, 30.0, 40.0, 50.0, float("inf")),
)
# fmt: on


def zem_metrics_middleware(get_response):
    def middleware(request):
        t0 = time.time()
        response = get_response(request)
        params = dict()
        params.update(common.extract_request_params(request))
        params.update(common.extract_response_params(response))
        REQUEST_TIMER.labels(**params).observe(time.time() - t0)
        return response

    return middleware
