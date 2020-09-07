from django.core.cache import caches

import utils.cache_helper

CACHE = "cluster_level_cache"
CACHE_PREFIX = "queryset_cached_count_"


class CachedCountMixin:
    def cached_count(self) -> int:
        cache_key = utils.cache_helper.get_cache_key(CACHE_PREFIX, str(self.query))
        count = caches[CACHE].get(cache_key)
        if not count:
            count = self.count()
            caches[CACHE].set(cache_key, count, timeout=180)
        return count
