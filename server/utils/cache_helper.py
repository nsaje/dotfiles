import hashlib


def get_cache_key(*args):
    if not args:
        raise Exception("Cache key creation requires at least one argument")

    h = hashlib.sha1()

    for arg in args:
        # arg can be a string, list or anything. First try with `unicode` because it can
        # encode more different obj types. It can fail though with strings, and this is
        # where decode comes in handy
        try:
            h.update(unicode(arg))
        except UnicodeEncodeError:
            h.update(arg.decode('utf-8', errors='ignore'))

    return h.hexdigest()
