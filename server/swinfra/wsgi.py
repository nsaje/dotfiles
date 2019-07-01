import prometheus_client

METRICS_PATH = "/internal/metrics"
SELFTEST_PATH = "/selftest"


class OutbrainWSGI:
    """
    A WSGI app (or wrapper) that provides common Outbrain endpoints like metrics and selftest.
    Will pass through requests to provided app if it's specified.
    """

    def __init__(self, app=None):
        self.base_app = app
        self.prometheus_app = prometheus_client.make_wsgi_app()

    def __call__(self, environ, start_response):
        path = environ["PATH_INFO"]
        if path == METRICS_PATH:
            return self.prometheus_app(environ, start_response)
        if path == SELFTEST_PATH:
            return self.selftest(environ, start_response)
        if self.base_app:
            return self.base_app(environ, start_response)
        return self.ret_404(environ, start_response)

    @staticmethod
    def selftest(environ, start_response):
        status = "200 OK"
        headers = [("Content-type", "text/plain")]
        start_response(status, headers)
        return [b"OK"]

    @staticmethod
    def ret_404(environ, start_response):
        status = "404 Not Found"
        headers = [("Content-type", "text/plain")]
        start_response(status, headers)
        return [b"Not found"]
