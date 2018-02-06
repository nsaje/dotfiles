import core.entity
import core.source
from .. import RealTimeDataHistory, RealTimeCampaignDataHistory
import dash.features.realtimestats

from utils import dates_helper


def refresh_realtime_data(campaigns=None):
    if not campaigns:
        campaigns = core.entity.Campaign.objects.filter(real_time_campaign_stop=True)
    _refresh_campaigns_realtime_data([campaign for campaign in campaigns if campaign.real_time_campaign_stop])


def _refresh_campaigns_realtime_data(campaigns):
    for campaign in campaigns:
        _refresh_ad_groups_realtime_data(campaign)
        _refresh_campaign_realtime_data(campaign)


def _refresh_ad_groups_realtime_data(campaign):
    for ad_group in campaign.adgroup_set.all().exclude_archived():
        try:
            stats = dash.features.realtimestats.get_ad_group_sources_stats(ad_group)
        except Exception:
            # TODO: handle failure to fetch data
            continue
        _add_ad_group_history_stats(ad_group, stats)


def _add_ad_group_history_stats(ad_group, stats):
    for stat in stats:
        source, spend = stat['source'], stat['spend']
        _add_source_stat(ad_group, source, spend)


def _add_source_stat(ad_group, source, spend):
    tz_today = dates_helper.utc_to_tz_datetime(
        dates_helper.utc_now(), source.source_type.budgets_tz).date()

    RealTimeDataHistory.objects.create(
        ad_group=ad_group,
        source=source,
        date=tz_today,
        etfm_spend=spend,
    )


def _refresh_campaign_realtime_data(campaign):
    _refresh_realtime_campaign_data_for_date(campaign, dates_helper.local_today())
    if _should_refresh_campaign_realtime_data_for_yesterday(campaign):
        _refresh_realtime_campaign_data_for_date(campaign, dates_helper.local_yesterday())


def _should_refresh_campaign_realtime_data_for_yesterday(campaign):
    local_today = dates_helper.local_today()
    any_source_tz_date_behind = any(
        dates_helper.tz_today(source_type.budgets_tz) < local_today
        for source_type in core.source.SourceType.objects.all())
    return any_source_tz_date_behind


def _refresh_realtime_campaign_data_for_date(campaign, date):
    spends = RealTimeDataHistory.objects.filter(
        ad_group__in=campaign.adgroup_set.all().exclude_archived(),
        date=date,
    ).distinct(
        'ad_group_id',
        'source_id',
    ).order_by(
        'ad_group_id',
        'source_id',
        '-created_dt'
    ).values_list('etfm_spend', flat=True)

    RealTimeCampaignDataHistory.objects.create(
        campaign=campaign,
        date=date,
        etfm_spend=sum(spends)
    )
