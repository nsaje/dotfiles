import threading

from django.dispatch import Signal

request_accessor = Signal()


class RequestProviderMiddleware(object):
    request_cache = {}

    def __init__(self):
        self._request = None
        request_accessor.connect(self)

    def process_request(self, request):
        self.request_cache[self._get_thread_id()] = request
        return None

    def process_response(self, request, response):
        self._delete()
        return response

    def _delete(self):
        thread_id = self._get_thread_id()
        del self.request_cache[thread_id]

    def __call__(self, **kwargs):
        return self.request_cache[self._get_thread_id()]

    def _get_thread_id(self):
        return threading.current_thread().ident


def get_request():
    return request_accessor.send(None)[0][1]
