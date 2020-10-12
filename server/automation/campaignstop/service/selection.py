import concurrent.futures
import random

from django.db import transaction
from django.db.models import BooleanField
from django.db.models import Case
from django.db.models import Count
from django.db.models import F
from django.db.models import When

import core.features.bcm
import core.models
import dash.constants
from utils import dates_helper
from utils import zlogging

from .. import CampaignStopState
from .. import RealTimeCampaignStopLog
from .. import RealTimeDataHistory
from .. import constants
from . import config
from . import refresh_realtime_data

logger = zlogging.getLogger(__name__)

LOG_MESSAGE = "Detected difference between max campaign calculations in campaignstop"
USE_AD_GROUP_DAILY_BUDGET = False


def mark_almost_depleted_campaigns(campaigns=None):
    if not campaigns:
        campaigns = core.models.Campaign.objects.filter(real_time_campaign_stop=True)

    campaigns = [campaign for campaign in campaigns if campaign.real_time_campaign_stop]
    _mark_almost_depleted_campaigns(campaigns)


def _mark_almost_depleted_campaigns(campaigns):
    _refresh_realtime_data(campaigns)
    available_campaign_budgets = _get_available_campaign_budgets(campaigns)
    max_campaign_spends = _get_max_campaign_spends(campaigns)

    _mark_campaigns(max_campaign_spends, available_campaign_budgets)


def _refresh_realtime_data(campaigns):
    random.shuffle(campaigns)
    with concurrent.futures.ThreadPoolExecutor(max_workers=config.JOB_PARALLELISM) as executor:
        executor.map(refresh_realtime_data, ([campaign] for campaign in campaigns))


def _get_available_campaign_budgets(campaigns):
    campaign_available_amount = {}
    date_to_digest = _get_date_to_digest()
    budget_line_items = _get_all_budget_line_items(campaigns)
    for budget_line_item in budget_line_items:
        campaign = budget_line_item.campaign
        campaign_available_amount.setdefault(campaign, 0)
        campaign_available_amount[campaign] += budget_line_item.get_available_etfm_amount(date=date_to_digest)
    return campaign_available_amount


def _get_all_budget_line_items(campaigns):
    today = dates_helper.local_today()
    return core.features.bcm.BudgetLineItem.objects.filter(
        campaign__in=campaigns, start_date__lte=today, end_date__gte=today
    ).select_related("campaign")


def _get_date_to_digest():
    if _in_critical_hours():
        day_before_yesterday = dates_helper.days_before(dates_helper.local_today(), 2)
        return day_before_yesterday
    return dates_helper.local_yesterday()


def _in_critical_hours():
    return 0 <= dates_helper.local_now().hour < config.HOURS_DELAY


def _get_max_campaign_spends(campaigns):
    max_campaign_spends = {}
    for campaign in campaigns:
        max_campaign_spends[campaign] = _calculate_max_campaign_spend(campaign)
    return max_campaign_spends


def _calculate_max_campaign_spend(campaign):
    rt_data = _get_latest_real_time_data(campaign)
    adg_source_spends, adg_spends = _get_rt_etfm_spends(rt_data)  # Change when aggregated adgroup datahistory exists
    ad_groups_map = _get_ad_groups_map(campaign)
    adg_sources_qs = _get_adgroup_sources_qs(campaign)
    spend_calculated_by_adg_source = _get_max_spend(ad_groups_map, adg_sources_qs, adg_source_spends)
    spend_calculated_by_adg = _get_max_spend_grouped_by_adg(ad_groups_map, adg_spends)
    if spend_calculated_by_adg_source != spend_calculated_by_adg:
        _log_differences(
            campaign.id,
            ad_groups_map,
            adg_sources_qs,
            adg_source_spends,
            adg_spends,
            spend_calculated_by_adg_source,
            spend_calculated_by_adg,
        )
    if USE_AD_GROUP_DAILY_BUDGET:  # I'll check the audience flag here to see which one to return
        return spend_calculated_by_adg
    return spend_calculated_by_adg_source


def _get_rt_etfm_spends(rt_data):
    adg_source_spends = {}
    adg_spends = {}
    for rtd in rt_data:
        adg_source_spends[(rtd.ad_group_id, rtd.source_id, rtd.date)] = rtd.etfm_spend
        adg_spends.setdefault((rtd.ad_group_id, rtd.date), 0)
        adg_spends[(rtd.ad_group_id, rtd.date)] += rtd.etfm_spend
    return adg_source_spends, adg_spends


def _get_ad_groups_map(campaign):
    return {
        ad_group["id"]: ad_group
        for ad_group in campaign.adgroup_set.annotate(
            inactive_count=Count(
                Case(When(adgroupsource__settings__state=dash.constants.AdGroupSourceSettingsState.INACTIVE, then=1))
            ),
            all_count=Count("adgroupsource__id"),
            has_active_source=Case(
                When(inactive_count=F("all_count"), then=False), default=True, output_field=BooleanField()
            ),
        ).values(
            "id",
            "settings__state",
            "settings__start_date",
            "settings__end_date",
            "settings__b1_sources_group_enabled",
            "settings__b1_sources_group_state",
            "settings__b1_sources_group_daily_budget",
            "settings__daily_budget",
            "has_active_source",
        )
    }


def _get_latest_real_time_data(campaign):
    return (
        RealTimeDataHistory.objects.filter(ad_group__campaign=campaign, date__gte=dates_helper.local_yesterday())
        .distinct("ad_group", "source", "date")
        .order_by("ad_group_id", "source_id", "-date", "-created_dt")
    )


def _get_adgroup_sources_qs(campaign):
    return core.models.AdGroupSource.objects.filter(ad_group__campaign=campaign).values(
        "ad_group_id", "source_id", "settings__state", "settings__daily_budget_cc", "source__source_type__type"
    )


def _mark_campaigns(campaign_daily_budgets, campaign_available_amount):
    for campaign in campaign_daily_budgets.keys():
        campaign_daily_budget = campaign_daily_budgets[campaign]
        available_amount = campaign_available_amount.get(campaign, 0)
        _mark_campaign(campaign, campaign_daily_budget, available_amount)


@transaction.atomic
def _mark_campaign(campaign, max_spend_today, available_budget_amount):
    min_remaining_budget = available_budget_amount - max_spend_today

    campaignstop_state, _ = CampaignStopState.objects.get_or_create(campaign=campaign)
    is_almost_depleted = (
        campaignstop_state.state == constants.CampaignStopState.ACTIVE and min_remaining_budget < config.THRESHOLD
    )
    campaignstop_state.update_almost_depleted(is_almost_depleted)

    log = RealTimeCampaignStopLog(campaign=campaign, event=constants.CampaignStopEvent.SELECTION_CHECK)
    log.add_context(
        {
            "min_remaining_budget": min_remaining_budget,
            "campaign_daily_budget": max_spend_today,
            "remaining_current_budget": available_budget_amount,
            "is_almost_depleted": is_almost_depleted,
        }
    )


def _get_max_spend(ad_groups_map, adg_sources_qs, adg_source_spends):
    b1_sources_group_spends = {}
    spend = 0
    today = dates_helper.local_today()
    for adg_source in adg_sources_qs.iterator():
        todays_realtime_spend = adg_source_spends.get((adg_source["ad_group_id"], adg_source["source_id"], today), 0)
        is_inactive_adg_source = adg_source["settings__state"] == dash.constants.AdGroupSettingsState.INACTIVE
        ad_group = ad_groups_map[adg_source["ad_group_id"]]

        if _in_critical_hours():
            yesterday = dates_helper.local_yesterday()
            yesterdays_realtime_spend = adg_source_spends.get(
                (adg_source["ad_group_id"], adg_source["source_id"], yesterday), 0
            )
            spend += yesterdays_realtime_spend

        is_b1_source_type = adg_source["source__source_type__type"] == dash.constants.SourceType.B1
        if is_b1_source_type and ad_group["settings__b1_sources_group_enabled"]:
            b1_sources_group_spends.setdefault(ad_group["id"], 0)
            b1_sources_group_spends[ad_group["id"]] += todays_realtime_spend
            if _in_critical_hours():
                b1_sources_group_spends[ad_group["id"]] += yesterdays_realtime_spend
            continue

        if not _is_active_setting(ad_group) or is_inactive_adg_source:
            spend += todays_realtime_spend
            continue

        settings_budget = adg_source["settings__daily_budget_cc"] or 0
        spend += max(settings_budget, todays_realtime_spend)

    spend += _b1_spends(ad_groups_map, b1_sources_group_spends)
    return spend


def _get_max_spend_grouped_by_adg(ad_groups_map, adg_spends):
    spend = 0
    today = dates_helper.local_today()
    for adg_id, adg_data in ad_groups_map.items():
        todays_realtime_spend = float(adg_spends.get((adg_id, today), 0))

        if _in_critical_hours():
            yesterday = dates_helper.local_yesterday()
            yesterdays_realtime_spend = float(adg_spends.get((adg_id, yesterday), 0))
            spend += yesterdays_realtime_spend

        if not _is_active_setting(adg_data) or not adg_data["has_active_source"]:
            spend += todays_realtime_spend
            continue

        settings_budget = adg_data["settings__daily_budget"] or 0
        spend += max(float(settings_budget), todays_realtime_spend)
    return spend


def _b1_spends(ad_groups_map, b1_sources_group_spends):
    spend = 0
    for ad_group_id, b1_group_spend in b1_sources_group_spends.items():
        ad_group = ad_groups_map[ad_group_id]
        is_group_state_inactive = (
            ad_group["settings__b1_sources_group_state"] == dash.constants.AdGroupSettingsState.INACTIVE
        )
        if not _is_active_setting(ad_group) or is_group_state_inactive:
            spend += b1_group_spend
            continue
        group_daily_budget = ad_group["settings__b1_sources_group_daily_budget"]
        spend += max(b1_group_spend, group_daily_budget)
    return spend


def _is_active_setting(ad_group):
    if ad_group["settings__state"] == dash.constants.AdGroupSettingsState.ACTIVE:
        today = dates_helper.local_today()
        start_date = ad_group["settings__start_date"]
        end_date = ad_group["settings__end_date"]
        if end_date is None:
            return start_date <= today
        else:
            return start_date <= today <= end_date
    return False


def _log_differences(
    campaign_id, ad_groups_map, adg_sources_qs, adg_source_spends, adg_spends, adg_source_calculation, adg_calculation
):
    logger.warning(
        LOG_MESSAGE,
        campaign=campaign_id,
        ad_groups_map=str(ad_groups_map),
        adg_sources_qs=str(adg_sources_qs),
        adg_source_spends=str(adg_source_spends),
        adg_spends=str(adg_spends),
        adg_source_calculation=adg_source_calculation,
        adg_calculation=adg_calculation,
    )
