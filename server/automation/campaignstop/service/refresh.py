import logging
import influx

import core.models
import core.features.yahoo_accounts
from .. import RealTimeDataHistory, RealTimeCampaignDataHistory
import dash.features.realtimestats
import dash.constants

from utils import dates_helper


logger = logging.getLogger(__name__)


CURRENT_DATA_LIMIT_SECONDS = 120


def refresh_if_stale(campaigns=None):
    if not campaigns:
        campaigns = core.models.Campaign.objects.filter(real_time_campaign_stop=True)
    rt_data = dict(
        RealTimeCampaignDataHistory.objects.filter(campaign__in=campaigns)
        .order_by("campaign_id", "-created_dt")
        .distinct("campaign_id")
        .values_list("campaign_id", "created_dt")
    )
    refresh_realtime_data(
        campaign for campaign in campaigns if campaign.real_time_campaign_stop and _is_stale(rt_data.get(campaign.id))
    )


def _is_stale(last_created_dt):
    if not last_created_dt:
        return True

    delta = dates_helper.utc_now() - last_created_dt
    return delta.total_seconds() > CURRENT_DATA_LIMIT_SECONDS


def refresh_realtime_data(campaigns=None):
    if not campaigns:
        campaigns = core.models.Campaign.objects.filter(real_time_campaign_stop=True)
    _refresh_campaigns_realtime_data([campaign for campaign in campaigns if campaign.real_time_campaign_stop])


def _refresh_campaigns_realtime_data(campaigns):
    for campaign in campaigns:
        _refresh_ad_groups_realtime_data(campaign)
        _refresh_campaign_realtime_data(campaign)


def _refresh_ad_groups_realtime_data(campaign):
    ad_groups = campaign.adgroup_set.all().select_related("campaign__account__yahoo_account").exclude_archived()
    for ad_group in ad_groups:
        try:
            stats = dash.features.realtimestats.get_ad_group_sources_stats_without_caching(ad_group, use_source_tz=True)
        except Exception:
            logger.exception("Failed refreshing realtime data for ad group: %s", ad_group.id)
            influx.incr("campaignstop.refresh.error", 1, level="adgroup")
            continue

        _add_ad_group_history_stats(ad_group, stats)


def _add_ad_group_history_stats(ad_group, stats):
    for stat in stats["stats"]:
        source, spend = stat["source"], stat["spend"]
        _add_source_stat(ad_group, source, spend)
    _log_source_errors(stats)


def _log_source_errors(stats):
    errors = stats.get("errors")
    if not errors:
        return

    for source, error in errors.items():
        influx.incr("campaignstop.refresh.error", 1, level="source", source=source)


def _add_source_stat(ad_group, source, spend):
    budgets_tz = dates_helper.DEFAULT_TIME_ZONE
    if source.source_type.type == dash.constants.SourceType.YAHOO:
        yahoo_account = ad_group.campaign.account.yahoo_account
        if yahoo_account:
            budgets_tz = yahoo_account.budgets_tz

    tz_today = dates_helper.tz_today(budgets_tz)
    RealTimeDataHistory.objects.create(ad_group=ad_group, source=source, date=tz_today, etfm_spend=spend)


def _refresh_campaign_realtime_data(campaign):
    _refresh_realtime_campaign_data_for_date(campaign, dates_helper.local_today())
    if _should_refresh_campaign_realtime_data_for_yesterday(campaign):
        _refresh_realtime_campaign_data_for_date(campaign, dates_helper.local_yesterday())


def _should_refresh_campaign_realtime_data_for_yesterday(campaign):
    local_today = dates_helper.local_today()
    yahoo_source_type = core.models.SourceType.objects.filter(
        source__adgroup__campaign_id=campaign.id, type=dash.constants.SourceType.YAHOO
    )
    if not yahoo_source_type.exists() or not campaign.account.yahoo_account:
        return False
    return dates_helper.tz_today(campaign.account.yahoo_account.budgets_tz) < local_today


def _refresh_realtime_campaign_data_for_date(campaign, date):
    spends = (
        RealTimeDataHistory.objects.filter(ad_group__in=campaign.adgroup_set.all().exclude_archived(), date=date)
        .distinct("ad_group_id", "source_id")
        .order_by("ad_group_id", "source_id", "-created_dt")
        .values_list("etfm_spend", flat=True)
    )

    RealTimeCampaignDataHistory.objects.create(campaign=campaign, date=date, etfm_spend=sum(spends))
