import decimal
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from operator import itemgetter

import core.features.bcm.calculations
from core.features import source_groups
from dash import models
from utils import k1_helper
from utils import metrics_compat
from utils import zlogging

logger = zlogging.getLogger(__name__)


def get_ad_group_stats(ad_group, use_local_currency=False):
    stats = _get_k1_source_stats(ad_group)
    _add_fees_and_margin(ad_group, stats["spend"])
    if use_local_currency:
        _to_local_currency(ad_group, stats["spend"])
    spend = sum(stat["spend"] for stat in stats["spend"])
    return {"spend": spend, "clicks": stats["clicks"], "impressions": stats["impressions"]}


def get_ad_group_sources_stats(ad_group, use_local_currency=False):
    stats = _get_ad_group_sources_stats(ad_group, use_local_currency=use_local_currency, spend_only=False)
    return {"spend": stats["spend"], "clicks": stats["clicks"], "impressions": stats["impressions"]}


def get_ad_group_sources_stats_without_caching(ad_group, use_local_currency=False):
    return _get_ad_group_sources_stats(ad_group, no_cache=True, use_local_currency=use_local_currency)


def _get_ad_group_sources_stats(ad_group, *, use_local_currency, no_cache=False, spend_only=True):
    stats = _get_k1_source_stats(ad_group, spend_only=spend_only, no_cache=no_cache)
    _clean_sources(ad_group, stats)
    _add_fees_and_margin(ad_group, stats["spend"])
    if use_local_currency:
        _to_local_currency(ad_group, stats["spend"])

    sources = models.Source.objects.all().select_related("source_type")
    sources_by_slug = {source.bidder_slug: source for source in sources}
    _augment_source(stats["spend"], sources_by_slug)

    stats["spend"] = sorted(stats["spend"], key=itemgetter("spend"), reverse=True)
    return stats


def _augment_source(stats, sources_by_slug):
    for stat in stats:
        if stat["source_slug"] in sources_by_slug:
            source = sources_by_slug[stat["source_slug"]]
            stat["source"] = source


def _clean_sources(ad_group, stats):
    source_slug_group_slug_map = source_groups.get_source_slug_group_slug_mapping()
    allowed_sources = set(
        models.AdGroupSource.objects.filter(ad_group=ad_group)
        .exclude(ad_review_only=True)
        .exclude(
            ad_group__campaign__account__agency__uses_source_groups=True,
            source__bidder_slug__in=source_slug_group_slug_map.keys(),
        )
        .values_list("source__bidder_slug", flat=True)
    )
    grouped_stats_spend = _group_stats_spend(ad_group, stats, source_slug_group_slug_map)

    cleaned_stats = []
    for stat in stats["spend"]:
        slug = stat["source_slug"]
        if slug not in allowed_sources:
            continue

        stat["spend"] += grouped_stats_spend.get(slug, 0)
        cleaned_stats.append(stat)

    stats["spend"] = cleaned_stats


def _group_stats_spend(ad_group, stats, source_slug_group_slug_map):
    if not ad_group.campaign.account.agency.uses_source_groups:
        return {}

    grouped_stats = defaultdict(float)
    for stat in stats["spend"]:
        group_slug = source_slug_group_slug_map.get(stat["source_slug"])
        if group_slug:
            grouped_stats[group_slug] += stat["spend"]

    return grouped_stats


def _add_fees_and_margin(ad_group, k1_stats):
    service_fee, license_fee, margin = ad_group.campaign.get_todays_fees_and_margin()
    for stat in k1_stats:
        stat["spend"] = core.features.bcm.calculations.apply_fees_and_margin(
            decimal.Decimal(stat["spend"]), service_fee, license_fee, margin
        )


def _to_local_currency(ad_group, stats):
    currency = ad_group.campaign.account.currency
    exchange_rate = core.features.multicurrency.get_current_exchange_rate(currency)
    for stat in stats:
        stat["spend"] = decimal.Decimal(stat["spend"]) * exchange_rate


def _get_k1_source_stats(ad_group, spend_only=False, no_cache=False):
    if no_cache:
        return _try_get_k1_source_stats(ad_group, spend_only, no_cache)
    return _get_k1_source_stats_with_error_handling(ad_group, spend_only)


def _get_k1_source_stats_with_error_handling(ad_group, spend_only):
    try:
        return _try_get_k1_source_stats(ad_group, spend_only)
    except urllib.error.HTTPError as e:
        metrics_compat.incr("dash.realtimestats.error", 1, type="http", status=str(e.code))
    except IOError:
        metrics_compat.incr("dash.realtimestats.error", 1, type="ioerror")
    except Exception as e:
        metrics_compat.incr("dash.realtimestats.error", 1, type="exception")
        logger.exception(e)
    return {"spend": []} if spend_only else {"spend": [], "clicks": 0, "impressions": 0}


def _try_get_k1_source_stats(ad_group, spend_only=False, no_cache=False):
    params = {}
    if no_cache:
        params["no_cache"] = True
    if spend_only:
        return k1_helper.get_adgroup_realtimestats_spend(ad_group.id, params)
    else:
        return k1_helper.get_adgroup_realtimestats(ad_group.id, params)
