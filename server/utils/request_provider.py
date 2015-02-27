import threading

from django.dispatch import Signal

request_accessor = Signal()


class RequestProviderMiddleware(object):
    request_cache = {}

    def __init__(self):
        self._request = None
        request_accessor.connect(self)

    def process_request(self, request):
        self.request_cache[self._get_thread_id()] = (request, True)
        return None

    def process_response(self, request, response):
        self._delete()
        return response

    def _delete(self):
        thread_id = self._get_thread_id()
        if self.request_cache[thread_id][1]:
            del self.request_cache[thread_id]

    def _mark_as_unsafe_to_delete(self):
        thread_id = self._get_thread_id()
        request, _ = self.request_cache[thread_id]

        self.request_cache[thread_id] = (request, False)

    def __call__(self, delete=False, unsafe_to_delete=False, **kwargs):
        if delete:
            self._delete()
        elif unsafe_to_delete:
            self._mark_as_unsafe_to_delete()
        else:
            return self.request_cache[self._get_thread_id()][0]

    def _get_thread_id(self):
        thread = threading.current_thread()

        while hasattr(thread, 'parent'):
            if thread == thread.parent:
                # prevent infinite cycling
                break

            thread = thread.parent

        return thread.ident


def get_request():
    return request_accessor.send(None)[0][1]


def mark_as_unsafe_to_delete():
    return request_accessor.send(None, unsafe_to_delete=True)[0][1]


def delete():
    return request_accessor.send(None, delete=True)[0][1]
