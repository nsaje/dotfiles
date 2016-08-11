import hashlib


def get_cache_key(*args):
    h = hashlib.sha1()

    if not args:
        raise Exception("Cache key creation requires at least one argument")

    for arg in args:
        h.update(unicode(arg))

    return h.hexdigest()
