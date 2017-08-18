import logging
from operator import itemgetter
import urllib2

import influx

from dash import constants, models
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
        source_types = [
            constants.SourceType.OUTBRAIN,
            constants.SourceType.YAHOO,
            constants.SourceType.FACEBOOK,
        ]
        ad_group_sources = (models.AdGroupSource.objects.select_related('source__source_type')
                            .filter(ad_group=ad_group)
                            .filter(source__source_type__type__in=source_types))

        params = {}
        for ad_group_source in ad_group_sources:
            if ad_group_source.source.source_type.type == constants.SourceType.OUTBRAIN \
                    and 'campaign_id' in ad_group_source.source_campaign_key:
                params['outbrain_campaign_id'] = ad_group_source.source_campaign_key['campaign_id']
            elif ad_group_source.source.source_type.type == constants.SourceType.YAHOO \
                    and ad_group_source.source_campaign_key:
                params['yahoo_campaign_id'] = ad_group_source.source_campaign_key
            elif ad_group_source.source.source_type.type == constants.SourceType.FACEBOOK \
                    and ad_group_source.source_campaign_key:
                params['facebook_campaign_id'] = ad_group_source.source_campaign_key

        stats = k1_helper.get_adgroup_realtimestats(ad_group.id, params)
    except urllib2.HTTPError as e:
        influx.incr('dash.realtimestats.error', 1, type='http', status=str(e.code))
        stats = []
    except Exception as e:
        influx.incr('dash.realtimestats.error', 1, type='exception')
        logger.exception(e)
        stats = []
    return stats


def _augment_source(stats, sources_by_slug):
    for stat in stats:
        if stat['source_slug'] in sources_by_slug:
            source = sources_by_slug[stat['source_slug']]
            stat['source'] = source.name
