from django.core.cache import caches

import core.models
from utils import k1_helper
from utils import outbrain_internal_helper
from utils import zlogging

logger = zlogging.getLogger(__name__)

CACHE_NAME = "cluster_level_cache"
CACHE_PREFIX = "adreviewlistener-"
CACHE_TIMEOUT = 7 * 24 * 60 * 60  # 7 days


def mark_ad_pending(content_ad_source):
    try:
        amplify_external_id = content_ad_source.source_content_ad_id
        amplify_internal_id = outbrain_internal_helper.to_internal_ids([amplify_external_id])[0]
        caches[CACHE_NAME].set(_get_cache_key(amplify_internal_id), content_ad_source.id, timeout=CACHE_TIMEOUT)
    except Exception:
        logger.exception("Could not mark ad as pending")


def ping_ad_if_relevant(amplify_internal_id):
    content_ad_source_id = caches[CACHE_NAME].get(_get_cache_key(amplify_internal_id))
    if content_ad_source_id:
        content_ad_source = core.models.ContentAdSource.objects.select_related("content_ad").get(
            pk=content_ad_source_id
        )
        k1_helper.update_content_ad(content_ad_source.content_ad, msg="adreviewlistener")


def _get_cache_key(internal_id):
    return CACHE_PREFIX + str(internal_id)
