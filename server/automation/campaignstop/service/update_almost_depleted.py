from django.db import transaction

import dash.constants
import core.entity
import core.bcm
from utils import dates_helper
from ..constants import CampaignStopEvent
from .. import CampaignStopState, RealTimeDataHistory, RealTimeCampaignStopLog
from . import refresh_realtime_data

HOURS_DELAY = 6


def mark_almost_depleted_campaigns(campaigns=None):
    if not campaigns:
        campaigns = core.entity.Campaign.objects.filter(real_time_campaign_stop=True)

    campaigns = [campaign for campaign in campaigns if campaign.real_time_campaign_stop]
    _mark_almost_depleted_campaigns(campaigns)


def _mark_almost_depleted_campaigns(campaigns):
    available_campaign_budgets = _get_available_campaign_budgets(campaigns)
    max_campaign_spends = _get_max_campaign_spends(campaigns)

    _mark_campaigns(max_campaign_spends, available_campaign_budgets)


def _get_available_campaign_budgets(campaigns):
    campaign_available_amount = {}
    date_to_digest = _get_date_to_digest()
    budget_line_items = _get_all_budget_line_items(campaigns)
    for budget_line_item in budget_line_items:
        campaign = budget_line_item.campaign
        campaign_available_amount.setdefault(campaign, 0)
        campaign_available_amount[campaign] += budget_line_item.get_available_etfm_amount(
            date=date_to_digest
        )
    return campaign_available_amount


def _get_all_budget_line_items(campaigns):
    today = dates_helper.local_today()
    return core.bcm.BudgetLineItem.objects.filter(
        campaign__in=campaigns,
        start_date__lte=today,
        end_date__gte=today,
    ).select_related('campaign')


def _get_date_to_digest():
    if _in_critical_hours():
        day_before_yesterday = dates_helper.days_before(dates_helper.local_today(), 2)
        return day_before_yesterday
    return dates_helper.local_yesterday()


def _in_critical_hours():
        return 0 <= dates_helper.local_now().hour < HOURS_DELAY


def _get_max_campaign_spends(campaigns):
    max_campaign_spends = {}
    for campaign in campaigns:
        max_campaign_spends[campaign] = _calculate_max_campaign_spend(campaign)
    return max_campaign_spends


def _calculate_max_campaign_spend(campaign):
    rt_data = _get_latest_real_time_data(campaign)
    adg_source_spends = _etfm_spends(rt_data)
    adg_sources = _get_adgroup_sources(campaign)
    return _get_max_spend(adg_sources, adg_source_spends)


def _get_latest_real_time_data(campaign):
    return RealTimeDataHistory.objects.filter(
        ad_group__campaign=campaign,
        date__gte=dates_helper.local_yesterday()
    ).distinct('ad_group', 'source', 'date').order_by('ad_group_id', 'source_id', '-date', '-created_dt')


def _get_adgroup_sources(campaign):
    return core.entity.AdGroupSource.objects.filter(ad_group__campaign=campaign).select_related(
        'settings', 'ad_group__settings', 'source__source_type'
    )


def _mark_campaigns(campaign_daily_budgets, campaign_available_amount):
    for campaign, campaign_daily_budget in campaign_daily_budgets.items():
        available_amount = campaign_available_amount.get(campaign, 0)
        _mark_campaign(campaign, campaign_daily_budget, available_amount)


@transaction.atomic
def _mark_campaign(campaign, max_spend_today, available_budget_amount):
    refresh_realtime_data([campaign])
    min_remaining_budget = available_budget_amount - max_spend_today
    is_almost_depleted = min_remaining_budget < 0

    _update_almost_depleted(campaign, is_almost_depleted)

    log = RealTimeCampaignStopLog(campaign=campaign, event=CampaignStopEvent.SELECTION_CHECK)
    log.add_context({
        'min_remaining_budget': min_remaining_budget,
        'campaign_daily_budget': max_spend_today,
        'remaining_current_budget': available_budget_amount,
        'is_almost_depleted': is_almost_depleted
    })


def _update_almost_depleted(campaign, is_almost_depleted):
    campaignstop_state, _ = CampaignStopState.objects.get_or_create(campaign=campaign)
    campaignstop_state.update_almost_depleted(is_almost_depleted)


def _get_max_spend(adg_sources, adg_source_spends):
    b1_sources_group_spends = {}
    spend = 0
    today = dates_helper.local_today()
    for adg_source in adg_sources:
        todays_realtime_spend = adg_source_spends.get((adg_source.ad_group_id, adg_source.source_id, today), 0)
        is_inactive_adg_source = adg_source.settings.state == dash.constants.AdGroupSettingsState.INACTIVE
        ad_group = adg_source.ad_group

        if _in_critical_hours():
            yesterday = dates_helper.local_yesterday()
            yesterdays_realtime_spend = adg_source_spends.get((adg_source.ad_group_id, adg_source.source_id, yesterday), 0)
            spend += yesterdays_realtime_spend

        is_b1_source_type = adg_source.source.source_type.type == dash.constants.SourceType.B1
        if is_b1_source_type and ad_group.settings.b1_sources_group_enabled:
            b1_sources_group_spends.setdefault(ad_group, 0)
            b1_sources_group_spends[ad_group] += todays_realtime_spend
            if _in_critical_hours():
                b1_sources_group_spends[ad_group] += yesterdays_realtime_spend
            continue

        if not _is_active_setting(ad_group.settings) or is_inactive_adg_source:
            spend += todays_realtime_spend
            continue

        settings_budget = adg_source.settings.daily_budget_cc or 0
        spend += max(settings_budget, todays_realtime_spend)

    spend += _b1_spends(b1_sources_group_spends)
    return spend


def _is_active_setting(ad_group_setting):
    if ad_group_setting.state == dash.constants.AdGroupSettingsState.ACTIVE:
        today = dates_helper.local_today()
        start_date = ad_group_setting.start_date
        end_date = ad_group_setting.end_date
        if end_date is None:
            return start_date <= today
        else:
            return start_date <= today <= end_date
    return False


def _b1_spends(b1_sources_group_spends):
    spend = 0
    for ad_group, b1_group_spend in b1_sources_group_spends.items():
        is_group_state_inactive = ad_group.settings.b1_sources_group_state == dash.constants.AdGroupSettingsState.INACTIVE
        if not _is_active_setting(ad_group.settings) or is_group_state_inactive:
            spend += b1_group_spend
            continue
        group_daily_budget = ad_group.settings.b1_sources_group_daily_budget
        spend += max(b1_group_spend, group_daily_budget)
    return spend


def _etfm_spends(rt_data):
    adg_source_spends = {}
    for rtd in rt_data:
        adg_source_spends[(rtd.ad_group_id, rtd.source_id, rtd.date)] = rtd.etfm_spend
    return adg_source_spends
