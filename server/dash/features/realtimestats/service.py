import decimal
import logging
from operator import itemgetter
import urllib2

import influx

from dash import constants, models
from utils import k1_helper
from utils import redirector_helper
from utils import dates_helper

import core.bcm.calculations


logger = logging.getLogger(__name__)


def get_ad_group_stats(ad_group):
    stats = _get_etfm_source_stats(ad_group)
    spend = sum(stat['spend'] for stat in stats)
    stats = {
        'spend': spend,
        'clicks': redirector_helper.get_adgroup_realtimestats(ad_group.id)['clicks'],
    }
    return stats


def get_ad_group_sources_stats(ad_group, use_source_tz=False):
    stats = _get_ad_group_sources_stats(ad_group, use_source_tz=use_source_tz)
    return stats


def get_ad_group_sources_stats_without_caching(ad_group, use_source_tz=False):
    return _get_ad_group_sources_stats(ad_group, no_cache=True, use_source_tz=use_source_tz)


def _get_ad_group_sources_stats(ad_group, no_cache=False, use_source_tz=False):
    stats = _get_etfm_source_stats(ad_group, no_cache=no_cache, use_source_tz=use_source_tz)

    sources = models.Source.objects.all().select_related('source_type')
    sources_by_slug = {source.bidder_slug: source for source in sources}
    _augment_source(stats, sources_by_slug)

    stats = sorted(stats, key=itemgetter('spend'), reverse=True)
    return stats


def _augment_source(stats, sources_by_slug):
    for stat in stats:
        if stat['source_slug'] in sources_by_slug:
            source = sources_by_slug[stat['source_slug']]
            stat['source'] = source


def _get_etfm_source_stats(ad_group, no_cache=False, use_source_tz=False):
    stats = _get_k1_source_stats(ad_group, no_cache=no_cache, use_source_tz=use_source_tz)
    _add_fee_and_margin(ad_group, stats)
    return stats


def _add_fee_and_margin(ad_group, k1_stats):
    if ad_group.campaign.account.uses_bcm_v2:
        fee, margin = ad_group.campaign.get_todays_fee_and_margin()
        for stat in k1_stats:
            stat['spend'] = core.bcm.calculations.apply_fee_and_margin(
                decimal.Decimal(stat['spend']),
                fee,
                margin,
            )


def _get_k1_source_stats(ad_group, no_cache=False, use_source_tz=False):
    if no_cache:
        return _try_get_k1_source_stats(ad_group, no_cache, use_source_tz=use_source_tz)
    return _get_k1_source_stats_with_error_handling(ad_group, use_source_tz=use_source_tz)


def _get_k1_source_stats_with_error_handling(ad_group, use_source_tz=False):
    try:
        return _try_get_k1_source_stats(ad_group, use_source_tz=use_source_tz)
    except urllib2.HTTPError as e:
        influx.incr('dash.realtimestats.error', 1, type='http', status=str(e.code))
        return []
    except IOError:
        influx.incr('dash.realtimestats.error', 1, type='ioerror')
        return []
    except Exception as e:
        influx.incr('dash.realtimestats.error', 1, type='exception')
        logger.exception(e)
        return []


def _try_get_k1_source_stats(ad_group, no_cache=False, use_source_tz=False):
    params = _get_params(ad_group, no_cache, use_source_tz=use_source_tz)
    stats = k1_helper.get_adgroup_realtimestats(ad_group.id, params)

    if 'stats' in stats:  # NOTE: support for k1 api change
        stats = stats['stats']
    return stats


def _get_params(ad_group, no_cache, use_source_tz=False):
    params = _get_source_params(ad_group, use_source_tz=use_source_tz)
    if no_cache:
        params['no_cache'] = True

    return params


def _get_source_params(ad_group, use_source_tz=False):
    source_types = [
        constants.SourceType.OUTBRAIN,
        constants.SourceType.YAHOO,
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
            if use_source_tz:
                params['yahoo_date'] = dates_helper.tz_today(
                    ad_group_source.source.source_type.budgets_tz).isoformat()

    return params
