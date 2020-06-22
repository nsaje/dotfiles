import decimal
import urllib.error
import urllib.parse
import urllib.request
from operator import itemgetter

import core.features.bcm.calculations
import core.features.yahoo_accounts
from dash import constants
from dash import models
from utils import dates_helper
from utils import k1_helper
from utils import metrics_compat
from utils import redirector_helper
from utils import zlogging

logger = zlogging.getLogger(__name__)


def get_ad_group_stats(ad_group, use_local_currency=False):
    stats = _get_etfm_source_stats(ad_group, use_local_currency=use_local_currency)
    spend = sum(stat["spend"] for stat in stats["stats"])
    stats = {"spend": spend, "clicks": redirector_helper.get_adgroup_realtimestats(ad_group.id)["clicks"]}
    return stats


def get_ad_group_sources_stats(ad_group, use_source_tz=False, use_local_currency=False):
    stats = _get_ad_group_sources_stats(ad_group, use_source_tz=use_source_tz, use_local_currency=use_local_currency)
    return stats["stats"]


def get_ad_group_sources_stats_without_caching(ad_group, use_source_tz=False, use_local_currency=False):
    return _get_ad_group_sources_stats(
        ad_group, no_cache=True, use_source_tz=use_source_tz, use_local_currency=use_local_currency
    )


def _get_ad_group_sources_stats(ad_group, *, use_local_currency, no_cache=False, use_source_tz=False):
    stats = _get_etfm_source_stats(
        ad_group, no_cache=no_cache, use_source_tz=use_source_tz, use_local_currency=use_local_currency
    )

    sources = models.Source.objects.all().select_related("source_type")
    sources_by_slug = {source.bidder_slug: source for source in sources}
    _augment_source(stats["stats"], sources_by_slug)

    stats["stats"] = sorted(stats["stats"], key=itemgetter("spend"), reverse=True)
    return stats


def _augment_source(stats, sources_by_slug):
    for stat in stats:
        if stat["source_slug"] in sources_by_slug:
            source = sources_by_slug[stat["source_slug"]]
            stat["source"] = source


def _get_etfm_source_stats(ad_group, *, use_local_currency, no_cache=False, use_source_tz=False):
    stats = _get_k1_source_stats(ad_group, no_cache=no_cache, use_source_tz=use_source_tz)
    _clean_sources(ad_group, stats)
    _add_fees_and_margin(ad_group, stats["stats"])
    if use_local_currency:
        _to_local_currency(ad_group, stats["stats"])
    return stats


def _clean_sources(ad_group, stats):
    allowed_sources = set(
        models.AdGroupSource.objects.filter(ad_group=ad_group)
        .exclude(ad_review_only=True)
        .values_list("source__bidder_slug", flat=True)
    )
    cleaned_stats = []
    for stat in stats["stats"]:
        if stat["source_slug"] not in allowed_sources:
            continue
        cleaned_stats.append(stat)
    stats["stats"] = cleaned_stats


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


def _get_k1_source_stats(ad_group, no_cache=False, use_source_tz=False):
    if no_cache:
        return _try_get_k1_source_stats(ad_group, no_cache, use_source_tz=use_source_tz)
    return _get_k1_source_stats_with_error_handling(ad_group, use_source_tz=use_source_tz)


def _get_k1_source_stats_with_error_handling(ad_group, use_source_tz=False):
    try:
        return _try_get_k1_source_stats(ad_group, use_source_tz=use_source_tz)
    except urllib.error.HTTPError as e:
        metrics_compat.incr("dash.realtimestats.error", 1, type="http", status=str(e.code))
    except IOError:
        metrics_compat.incr("dash.realtimestats.error", 1, type="ioerror")
    except Exception as e:
        metrics_compat.incr("dash.realtimestats.error", 1, type="exception")
        logger.exception(e)
    return {"stats": []}


def _try_get_k1_source_stats(ad_group, no_cache=False, use_source_tz=False):
    params = _get_params(ad_group, no_cache, use_source_tz=use_source_tz)
    return k1_helper.get_adgroup_realtimestats(ad_group.id, params)


def _get_params(ad_group, no_cache, use_source_tz=False):
    params = _get_source_params(ad_group, use_source_tz=use_source_tz)
    if no_cache:
        params["no_cache"] = True

    return params


def _get_source_params(ad_group, use_source_tz=False):
    source_types = [constants.SourceType.OUTBRAIN, constants.SourceType.YAHOO]
    ad_group_sources = (
        models.AdGroupSource.objects.select_related("source__source_type")
        .filter(ad_group=ad_group)
        .exclude(ad_review_only=True)
        .filter(source__source_type__type__in=source_types)
    )

    params = {}
    for ad_group_source in ad_group_sources:
        if (
            ad_group_source.source.source_type.type == constants.SourceType.OUTBRAIN
            and "campaign_id" in ad_group_source.source_campaign_key
        ):
            params["outbrain_campaign_id"] = ad_group_source.source_campaign_key["campaign_id"]
        elif (
            ad_group_source.source.source_type.type == constants.SourceType.YAHOO
            and ad_group_source.source_campaign_key
        ):
            params.update(
                {
                    "yahoo_advertiser_id": ad_group.campaign.account.yahoo_account.advertiser_id,
                    "yahoo_campaign_id": ad_group_source.source_campaign_key,
                }
            )
            if use_source_tz:
                yahoo_account = ad_group.campaign.account.yahoo_account
                if yahoo_account:
                    params["yahoo_date"] = dates_helper.tz_today(yahoo_account.budgets_tz).isoformat()

    return params
