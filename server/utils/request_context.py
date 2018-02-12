import threading
import copy


_threadlocal = threading.local()


def set(key, value):
    setattr(_threadlocal, key, value)


def get(key, default=None):
    return getattr(_threadlocal, key, default)


def get_dict():
    return copy.deepcopy(_threadlocal.__dict__)


def set_dict(d):
    for key, value in list(d.items()):
        setattr(_threadlocal, key, value)
