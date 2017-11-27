import core.entity
from .. import RealTimeDataHistory

from utils import dates_helper
import dash.features.realtimestats


def refresh_realtime_data(campaigns=None):
    if not campaigns:
        campaigns = core.entity.Campaign.objects.filter(real_time_campaign_stop=True)
    _refresh_campaigns_realtime_data(campaigns)


def _refresh_campaigns_realtime_data(campaigns):
    for campaign in campaigns:
        _refresh_ad_groups_realtime_data(
            campaign.adgroup_set.all().exclude_archived()
        )


def _refresh_ad_groups_realtime_data(ad_groups):
    for ad_group in ad_groups:
        try:
            stats = dash.features.realtimestats.service.get_ad_group_sources_stats(ad_group)
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
