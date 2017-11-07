import threading
import functools

threadlocal = threading.local()


class use_read_replica(object):

    def __enter__(self):
        setattr(threadlocal, 'USE_READ_REPLICA', True)

    def __exit__(self, exc_type, exc_value, traceback):
        setattr(threadlocal, 'USE_READ_REPLICA', None)

    def __call__(self, func):
        @functools.wraps(func)
        def inner(*args, **kwargs):
            with self:
                return func(*args, **kwargs)
        return inner


def get_thread_local(attr, default=None):
    return getattr(threadlocal, attr, default)
