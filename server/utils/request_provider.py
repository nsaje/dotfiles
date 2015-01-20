import threading
import weakref

from django.dispatch import Signal

request_accessor = Signal()


class RequestProviderMiddleware(object):
    request_cache = weakref.WeakValueDictionary()

    def __init__(self):
        self._request = None
        request_accessor.connect(self)

    def process_request(self, request):
        self.request_cache[self.get_thread_id()] = request
        return None

    def __call__(self, **kwargs):
        return self.request_cache[self.get_thread_id()]

    def get_thread_id(self):
        thread = threading.current_thread()

        while hasattr(thread, 'parent'):
            if thread == thread.parent:
                # prevent infinite cycling
                break

            thread = thread.parent

        return thread.ident


def get_request():
    return request_accessor.send(None)[0][1]
