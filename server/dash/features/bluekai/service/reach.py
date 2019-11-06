from django.core.cache import caches

from utils import cache_helper
from utils import zlogging

from . import bluekaiapi

logger = zlogging.getLogger(__name__)


CACHE_TIMEOUT = 3 * 24 * 60 * 60  # 3 days


def _get_reach(expression):
    cache = caches["dash_db_cache"]
    cache_key = cache_helper.get_cache_key("bluekai_reach", expression)
    cached = cache.get(cache_key)
    if cached:
        return cached

    reach = bluekaiapi.get_segment_reach(expression)
    ret = {"value": reach, "relative": calculate_relative_reach(reach)}

    cache.set(cache_key, ret, timeout=CACHE_TIMEOUT)
    return ret


def get_reach(expression):
    try:
        return _get_reach(expression)
    except Exception:
        logger.exception("Exception occured when fetching reach from BlueKai")
        return None


def calculate_relative_reach(reach):
    if not reach:
        return 0

    x = float(reach) / pow(10, 7)
    relative = 1 - (1 / (x + 1))
    return int(relative * 100)
