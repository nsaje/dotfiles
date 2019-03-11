import datetime
import logging
from collections import defaultdict

from django.db.models import Q

import core.features.bcm

import dash
import dash.constants
import dash.models
from automation import campaignstop

from . import settings

logger = logging.getLogger(__name__)


def get_active_ad_groups_on_autopilot(autopilot_state=None):
    states = [autopilot_state]
    if not autopilot_state:
        states = [
            dash.constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET,
            dash.constants.AdGroupSettingsAutopilotState.ACTIVE_CPC,
        ]

    ad_groups_on_autopilot = []
    ad_group_settings_on_autopilot = []
    ad_group_settings = (
        dash.models.AdGroupSettings.objects.all().group_current_settings().select_related("ad_group__campaign")
    )
    campaignstop_states = campaignstop.get_campaignstop_states(dash.models.Campaign.objects.all())

    for ags in ad_group_settings:
        if ags.autopilot_state in states:
            ad_group = ags.ad_group
            ad_groups_sources_settings = dash.models.AdGroupSourceSettings.objects.filter(
                ad_group_source__ad_group=ad_group
            ).group_current_settings()

            ad_group_running = ad_group.get_running_status(ags) == dash.constants.AdGroupRunningStatus.ACTIVE
            sources_running = (
                ad_group.get_running_status_by_sources_setting(ags, ad_groups_sources_settings)
                == dash.constants.AdGroupRunningStatus.ACTIVE
            )
            campaign_active = campaignstop_states[ad_group.campaign.id]["allowed_to_run"]
            if campaign_active and ad_group_running and sources_running:
                ad_groups_on_autopilot.append(ad_group)
                ad_group_settings_on_autopilot.append(ags)
    return ad_groups_on_autopilot, ad_group_settings_on_autopilot


def get_autopilot_entities(ad_group=None, campaign=None):
    states = [
        dash.constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET,
        dash.constants.AdGroupSettingsAutopilotState.ACTIVE_CPC,
    ]
    ad_groups = (
        dash.models.AdGroup.objects.all()
        .filter(Q(settings__autopilot_state__in=states) | Q(campaign__settings__autopilot=True))
        .select_related("settings", "campaign__settings", "campaign__account")
        .distinct()
    )
    if ad_group is not None:
        ad_groups = ad_groups.filter(id=ad_group.id)
    elif campaign is not None:
        ad_groups = ad_groups.filter(campaign=campaign)
    else:
        ad_groups = ad_groups.filter_active()

    campaignstop_states = campaignstop.get_campaignstop_states(
        dash.models.Campaign.objects.filter(adgroup__in=ad_groups)
    )
    ad_group_sources = (
        dash.models.AdGroupSource.objects.all()
        .filter(settings__state=dash.constants.AdGroupSourceSettingsState.ACTIVE)
        .filter(ad_group_id__in=[ag.id for ag in ad_groups])
        .exclude(ad_review_only=True)
        .select_related("source__source_type")
        .select_related("settings")
        .order_by("pk")
    )
    ags_per_ag_id = defaultdict(list)
    for ags in ad_group_sources:
        ags_per_ag_id[ags.ad_group_id].append(ags)

    data = defaultdict(dict)
    for ag in ad_groups:
        if _should_exclude_ad_group(ag, campaignstop_states, ad_group, campaign):
            continue

        ags = ags_per_ag_id[ag.id]
        if (
            ag.settings.b1_sources_group_enabled
            and ag.settings.b1_sources_group_state == dash.constants.AdGroupSourceSettingsState.INACTIVE
        ):
            ags = _exclude_b1_ad_group_sources(ags)

        if len(ags) == 0:
            continue

        # cache optimization (loading adgroup source and adgroup settings in single query is too slow)
        for ad_group_source in ags:
            ad_group_source.ad_group = ag

        data[ag.campaign][ag] = ags

    return data


def _should_exclude_ad_group(ag, campaignstop_states, ad_group, campaign):
    # always process on setting change and not campaign autopilot
    if (ad_group is not None or campaign is not None) and not ag.campaign.settings.autopilot:
        return False

    # do not process when adgroup not running
    if ag.get_running_status(ag.settings) != dash.constants.AdGroupRunningStatus.ACTIVE:
        return True

    # on setting change and campaign autopilot process everything but paused adgroups
    if ad_group is not None or campaign is not None:
        return False

    # do not process adgroups stopped by campaign stop on daily runs
    if ag.campaign.id not in campaignstop_states or not campaignstop_states[ag.campaign.id]["allowed_to_run"]:
        return True


def _exclude_b1_ad_group_sources(ad_group_sources):
    return [ags for ags in ad_group_sources if ags.source.source_type.type != dash.constants.SourceType.B1]


def get_autopilot_active_sources_settings(
    ad_groups_and_settings, ad_group_setting_state=dash.constants.AdGroupSettingsState.ACTIVE
):
    adgroup_sources = (
        dash.models.AdGroupSource.objects.filter(ad_group__in=list(ad_groups_and_settings.keys()))
        .filter(ad_group__settings__archived=False)
        .select_related("settings__ad_group_source__source__source_type")
        .select_related("settings__ad_group_source__ad_group__campaign__account")
    )

    if not ad_group_setting_state:
        return [ags.settings for ags in ad_group_setting_state]

    ret = []
    for ags in adgroup_sources:
        agss = ags.settings
        ad_group_settings = ad_groups_and_settings[agss.ad_group_source.ad_group]
        if ad_group_setting_state == dash.constants.AdGroupSettingsState.ACTIVE:
            if (
                agss.ad_group_source.source.source_type.type == dash.constants.SourceType.B1
                and ad_group_settings.b1_sources_group_enabled
                and ad_group_settings.b1_sources_group_state == dash.constants.AdGroupSourceSettingsState.INACTIVE
            ):
                continue
        elif ad_group_setting_state == dash.constants.AdGroupSettingsState.INACTIVE:
            if (
                agss.ad_group_source.source.source_type.type == dash.constants.SourceType.B1
                and ad_group_settings.b1_sources_group_enabled
                and ad_group_settings.b1_sources_group_state == dash.constants.AdGroupSourceSettingsState.ACTIVE
            ):
                continue

        if agss.state == ad_group_setting_state:
            ret.append(agss)

    return ret


def ad_group_source_is_synced(ad_group_source):
    min_sync_date = datetime.datetime.utcnow() - datetime.timedelta(hours=settings.SYNC_IS_RECENT_HOURS)
    last_sync = ad_group_source.last_successful_sync_dt
    if last_sync is None:
        return False
    return last_sync >= min_sync_date


def update_ad_group_source_values(ad_group_source, changes, system_user=None):
    ad_group_source.settings.update(
        system_user=system_user, k1_sync=False, skip_automation=True, skip_validation=True, **changes
    )


def update_ad_group_b1_sources_group_values(ad_group, changes, system_user=None):
    kwargs = {}

    if "cpc_cc" in changes:
        kwargs["b1_sources_group_cpc_cc"] = changes["cpc_cc"]

    if "cpm" in changes:
        kwargs["b1_sources_group_cpm"] = changes["cpm"]

    if "daily_budget_cc" in changes:
        kwargs["b1_sources_group_daily_budget"] = changes["daily_budget_cc"]

    if not kwargs:
        return

    ad_group.settings.update(None, skip_validation=True, system_user=system_user, **kwargs)


def get_ad_group_sources_minimum_bid(ad_group_source, bcm_modifiers):
    if ad_group_source.ad_group.bidding_type == dash.constants.BiddingType.CPM:
        etfm_min_bid = ad_group_source.source.source_type.get_etfm_min_cpm(bcm_modifiers)
        autopilot_min_bid = settings.AUTOPILOT_MIN_CPM
    else:
        etfm_min_bid = ad_group_source.source.source_type.get_etfm_min_cpc(bcm_modifiers)
        autopilot_min_bid = settings.AUTOPILOT_MIN_CPC
    return max(autopilot_min_bid, etfm_min_bid or 0)


def get_ad_group_sources_minimum_daily_budget(ad_group_source, uses_bcm_v2, bcm_modifiers):
    source_min_daily_budget = ad_group_source.source.source_type.get_etfm_min_daily_budget(bcm_modifiers)
    ap_settings_min_budget = settings.BUDGET_AP_MIN_SOURCE_BUDGET
    if uses_bcm_v2:
        ap_settings_min_budget = core.features.bcm.calculations.calculate_min_daily_budget(
            ap_settings_min_budget, bcm_modifiers
        )
    if not source_min_daily_budget:
        return ap_settings_min_budget
    return max(ap_settings_min_budget, source_min_daily_budget)


def get_campaign_goal_column(campaign_goal, uses_bcm_v2=False):
    if campaign_goal:
        column_definition = settings.GOALS_COLUMNS[campaign_goal.type]
        if uses_bcm_v2 and "col_bcm_v2" in column_definition:
            return column_definition["col_bcm_v2"]
        return column_definition["col"]


def get_campaign_goal_column_importance(campaign_goal):
    if campaign_goal:
        return settings.GOALS_COLUMNS[campaign_goal.type]["importance"]
