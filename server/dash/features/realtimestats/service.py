import logging
from operator import itemgetter

from dash import models
from utils import k1_helper
from utils import redirector_helper

logger = logging.getLogger(__name__)


def get_ad_group_stats(ad_group):
    stats = {
        'spend': sum(stat['spend'] for stat in _get_k1_adgroup_stats(ad_group)),
        'clicks': redirector_helper.get_adgroup_realtimestats(ad_group.id)['clicks'],
    }
    return stats


def get_ad_group_sources_stats(ad_group):
    stats = _get_k1_adgroup_stats(ad_group)

    sources = models.Source.objects.all()
    sources_by_slug = {source.bidder_slug: source for source in sources}
    _augment_source(stats, sources_by_slug)

    stats = sorted(stats, key=itemgetter('spend'), reverse=True)

    return stats


def _get_k1_adgroup_stats(ad_group):
    try:
        stats = k1_helper.get_adgroup_realtimestats(ad_group.id)
    except Exception as e:
        logger.exception(e)
        stats = []
    return stats


def _augment_source(stats, sources_by_slug):
    for stat in stats:
        if stat['source_slug'] in sources_by_slug:
            source = sources_by_slug[stat['source_slug']]
            stat['source'] = source.name
