import collections
import hashlib

from django.db.models.query import QuerySet
from django.db.models import Model


def get_cache_key(*args, **kwargs):
    if not args:
        raise Exception("Cache key creation requires at least one argument")

    h = hashlib.sha1()

    serialized = _serialize((args, kwargs))
    h.update(serialized.encode("utf-8", errors="ignore"))

    return h.hexdigest()


def _serialize(value, postfix="", prefix=""):
    serialized = prefix

    if isinstance(value, QuerySet):
        serialized += _serialize(
            sorted(value.values_list("id", flat=True)), ")", "QuerySet<" + value.model.__name__ + ">("
        )
    elif isinstance(value, Model):
        serialized += value.__class__.__name__ + "(" + str(value.pk) + ")"
    elif isinstance(value, collections.OrderedDict):
        serialized += "OrderedDict({"
        for k, v in list(value.items()):
            serialized += _serialize(k, ":")
            serialized += _serialize(v, ",")
        serialized += "})"
    elif hasattr(value, "__dict__"):
        serialized += _serialize(value.__dict__, ")", value.__class__.__name__ + "(")
    elif isinstance(value, dict):
        serialized += "{"
        for k, v in sorted(value.items()):
            serialized += _serialize(k, ":")
            serialized += _serialize(v, ",")
        serialized += "}"
    elif isinstance(value, (str,)):
        serialized += value
    elif isinstance(value, collections.Iterable):
        serialized += "["
        for x in value:
            serialized += _serialize(x, ",")
        serialized += "]"
    else:
        try:
            serialized += str(value)
        except UnicodeEncodeError:
            serialized += value.decode("utf-8", errors="ignore")

    serialized += postfix
    return serialized
