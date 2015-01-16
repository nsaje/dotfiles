import sys
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
        ''' Returns the thread ID of the current thread or greenlet ID if running
        in greenlet.
        '''
        greenlet = sys.modules.get('greenlet')
        if greenlet:
            current_greenlet = greenlet.getcurrent()
            if current_greenlet is not None and current_greenlet.parent:
                return id(current_greenlet)

        return threading.current_thread().ident


def get_request():
    return request_accessor.send(None)[0][1]
