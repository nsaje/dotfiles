import datetime
import traceback
from collections import defaultdict
from decimal import Decimal

from django.db import transaction

import dash.constants
import dash.models
import etl.materialization_run
import prodops.hacks.constants as hack_constants
import redshiftapi.api_breakdowns
from automation import models
from utils import dates_helper
from utils import k1_helper
from utils import metrics_compat
from utils import pagerduty_helper
from utils import slack
from utils import zlogging

from . import bid
from . import budgets
from . import constants
from . import helpers
from . import prefetch
from .campaign import calculate_campaigns_daily_budget

logger = zlogging.getLogger(__name__)

SKIP_CAMPAIGN_BID_AUTOPILOT_AGENCIES = (hack_constants.AGENCY_RCS_ID, hack_constants.AGENCY_ZMS_VIDEO_ID)


@metrics_compat.timer("automation.autopilot_plus_legacy.run_autopilot")
def run_autopilot(
    ad_group=None,
    campaign=None,
    adjust_bids=True,
    adjust_budgets=True,
    initialization=False,
    report_to_influx=False,
    dry_run=False,
    daily_run=False,
):
    processed_ad_group_ids = None
    if daily_run:
        # after EST midnight wait 2h for data to be available + 3h for refresh_etl to complete
        from_date_time = dates_helper.local_midnight_to_utc_time().replace(tzinfo=None) + datetime.timedelta(hours=5)

        if not etl.materialization_run.etl_data_complete_for_date(dates_helper.local_yesterday()):
            logger.info("Autopilot daily run was aborted since materialized data is not yet available.")
            return

        processed_ad_group_ids = helpers.get_processed_autopilot_ad_group_ids(from_date_time)

        if processed_ad_group_ids:
            logger.info("Excluding processed ad groups", num_excluded=len(processed_ad_group_ids))

    entities = helpers.get_autopilot_entities(
        ad_group=ad_group, campaign=campaign, excluded_ad_group_ids=processed_ad_group_ids
    )
    if ad_group is None:  # do not calculate campaign budgets when run for one ad_group only
        campaign_daily_budgets = calculate_campaigns_daily_budget(campaign=campaign)

    data, campaign_goals, bcm_modifiers_map = prefetch.prefetch_autopilot_data(entities)
    if not data:
        return {}
    changes_data = {}

    failed_campaigns = []
    failed_ad_groups = []

    for campaign, ad_groups in entities.items():
        try:
            ad_groups = _filter_adgroups_with_data(ad_groups, data)
            if campaign.settings.autopilot:
                budget_changes_map = _get_budget_predictions_for_campaign(
                    campaign,
                    ad_groups,
                    campaign_daily_budgets[campaign],
                    data,
                    bcm_modifiers_map.get(campaign),
                    campaign_goals.get(campaign, {}),
                    adjust_budgets,
                )
                bid_changes_map = {}
                for ad_group in ad_groups:
                    try:
                        bid_changes_map[ad_group] = _get_bid_predictions(
                            ad_group,
                            budget_changes_map[ad_group],
                            data[ad_group],
                            bcm_modifiers_map.get(campaign),
                            adjust_bids,
                            campaign_goals.get(campaign, {}),
                            is_budget_ap_enabled=True,
                        )
                        changes_data = _get_autopilot_campaign_changes_data(
                            ad_group, changes_data, bid_changes_map[ad_group], budget_changes_map[ad_group]
                        )
                    except Exception:
                        logger.exception(
                            "Autopilot failed operating on autopilot campaign's ad group %s", str(ad_group)
                        )
                        failed_ad_groups.append(ad_group)

                campaign_failed_ad_groups = _save_changes_campaign(
                    campaign, ad_groups, data, campaign_goals, budget_changes_map, bid_changes_map, dry_run, daily_run
                )

                if campaign_failed_ad_groups:
                    failed_ad_groups.extend(campaign_failed_ad_groups)

            else:
                for ad_group in ad_groups:
                    try:
                        budget_changes = _get_budget_predictions_for_adgroup(
                            ad_group,
                            data[ad_group],
                            bcm_modifiers_map.get(campaign),
                            campaign_goals.get(campaign, {}),
                            adjust_budgets,
                            daily_run,
                        )
                        bid_changes = _get_bid_predictions(
                            ad_group,
                            budget_changes,
                            data[ad_group],
                            bcm_modifiers_map.get(campaign),
                            adjust_bids,
                            campaign_goals.get(campaign, {}),
                        )
                        _save_changes(data, campaign_goals, ad_group, budget_changes, bid_changes, dry_run, daily_run)
                        changes_data = _get_autopilot_campaign_changes_data(
                            ad_group, changes_data, bid_changes, budget_changes
                        )
                    except Exception:
                        logger.exception("Autopilot failed operating on ad group", ad_group_id=str(ad_group))
                        failed_ad_groups.append(ad_group)

        except Exception:
            logger.exception("Autopilot failed operating on campaign", campaign_id=str(campaign))
            failed_campaigns.append(campaign)

    if failed_campaigns:
        details = "\n".join(["- {}".format(slack.campaign_url(campaign)) for campaign in failed_campaigns])
        slack.publish(
            "Autopilot run failed for the following campaigns:\n{}".format(details),
            channel=slack.CHANNEL_RND_Z1_ALERTS_AUX,
            msg_type=slack.MESSAGE_TYPE_CRITICAL,
            username=slack.USER_AUTOPILOT,
        )

    if failed_ad_groups:
        details = "\n".join(["- {}".format(slack.ad_group_url(ad_group)) for ad_group in failed_ad_groups])
        slack.publish(
            "Autopilot run failed for the following ad groups:\n{}".format(details),
            channel=slack.CHANNEL_RND_Z1_ALERTS_AUX,
            msg_type=slack.MESSAGE_TYPE_CRITICAL,
            username=slack.USER_AUTOPILOT,
        )

    if report_to_influx:
        # refresh entities from db so we report new data, always report data for all entities
        entities = helpers.get_autopilot_entities()
        _report_adgroups_data_to_influx(entities, campaign_daily_budgets)
        _report_new_budgets_on_ap_to_influx(entities)
    return changes_data


@transaction.atomic
def _save_changes_campaign(
    campaign, ad_groups, data, campaign_goals, budget_changes_map, bid_changes_map, dry_run, daily_run
):
    if dry_run:
        return

    failed_ad_groups = []
    for ad_group in ad_groups:
        try:
            _save_changes(
                data,
                campaign_goals,
                ad_group,
                budget_changes_map[ad_group],
                bid_changes_map[ad_group],
                dry_run,
                daily_run,
                campaign=campaign,
            )
        except Exception:
            logger.exception(
                "Autopilot failed saving changes on autopilot campaign's ad group", ad_group_id=str(ad_group)
            )
            failed_ad_groups.append(ad_group)

    return failed_ad_groups


def _save_changes(data, campaign_goals, ad_group, budget_changes, bid_changes, dry_run, daily_run, campaign=None):
    if dry_run:
        return

    with transaction.atomic():
        set_autopilot_changes(bid_changes, budget_changes, ad_group, dry_run=dry_run)
        persist_autopilot_changes_to_log(
            ad_group,
            bid_changes,
            budget_changes,
            data[ad_group],
            ad_group.settings.autopilot_state,
            campaign_goals.get(ad_group.campaign),
            is_autopilot_job_run=daily_run,
            campaign=campaign,
        )
    k1_helper.update_ad_group(ad_group, "run_autopilot")


def _filter_adgroups_with_data(ad_groups, data):
    result = {}
    for ad_group, value in ad_groups.items():
        if ad_group not in data:
            logger.warning("Data for ad group not prefetched in AP", ad_group_id=str(ad_group))
            continue
        result[ad_group] = value
    return result


def _get_budget_predictions_for_adgroup(ad_group, data, bcm_modifiers, campaign_goal, adjust_budgets, daily_run):
    if ad_group.settings.autopilot_state != dash.constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET:
        return {}
    if not adjust_budgets:
        return {}

    return budgets.get_autopilot_daily_budget_recommendations(
        ad_group,
        ad_group.settings.autopilot_daily_budget,
        _filter_data_budget_ap_allrtb(data, ad_group),
        bcm_modifiers,
        campaign_goal.get("goal"),
    )


def _get_budget_predictions_for_campaign(
    campaign, ad_groups, daily_budget, data, bcm_modifiers, campaign_goal, adjust_budgets
):
    if not campaign.settings.autopilot:
        return {}
    if not adjust_budgets:
        return {}

    campaign_data = {}
    for ad_group in ad_groups:
        campaign_data.update(_filter_data_budget_ap_allrtb(data[ad_group], ad_group))

    changes = budgets.get_autopilot_daily_budget_recommendations(
        campaign,
        daily_budget,
        campaign_data,
        bcm_modifiers,
        campaign_goal.get("goal"),
        ignore_daily_budget_too_small=True,
    )

    grouped_changes = defaultdict(dict)
    for ad_group_source, change in changes.items():
        grouped_changes[ad_group_source.ad_group][ad_group_source] = change

    return grouped_changes


def _filter_data_budget_ap_allrtb(data, ad_group):
    if ad_group.settings.b1_sources_group_enabled:
        data = {
            ags: v
            for ags, v in data.items()
            if ags.source == dash.models.AllRTBSource or ags.source.source_type.type != dash.constants.SourceType.B1
        }
    return data


def _get_bid_predictions(
    ad_group, budget_changes, data, bcm_modifiers, adjust_bids, campaign_goal, is_budget_ap_enabled=False
):
    if not _can_run_bid_autopilot(ad_group.campaign):
        return {}
    bid_changes = {}
    rtb_as_one = ad_group.settings.b1_sources_group_enabled
    active_bid_budget = dash.constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET
    is_budget_ap_enabled = ad_group.settings.autopilot_state == active_bid_budget or is_budget_ap_enabled
    if adjust_bids:
        goal = campaign_goal.get("goal")
        adjust_rtb_sources = not rtb_as_one or (
            goal and goal.type == dash.constants.CampaignGoalKPI.CPA and is_budget_ap_enabled
        )
        bid_changes = bid.get_autopilot_bid_recommendations(
            ad_group,
            data,
            bcm_modifiers,
            campaign_goal,
            budget_changes=budget_changes,
            adjust_rtb_sources=adjust_rtb_sources,
        )
    return bid_changes


def _can_run_bid_autopilot(campaign):
    if campaign.account.agency_id in SKIP_CAMPAIGN_BID_AUTOPILOT_AGENCIES:
        return False
    return True


def recalculate_budgets_ad_group(ad_group):
    changed_sources = set()
    if ad_group.campaign.settings.autopilot:
        run_autopilot(campaign=ad_group.campaign, adjust_bids=False, adjust_budgets=True, initialization=True)
    else:
        paused_sources_changes = _set_paused_ad_group_sources_to_minimum_values(
            ad_group, ad_group.campaign.get_bcm_modifiers()
        )
        autopilot_changes_data = run_autopilot(
            ad_group=ad_group, adjust_bids=False, adjust_budgets=True, initialization=True
        )

        for source, changes in paused_sources_changes.items():
            if changes["old_budget"] != changes["new_budget"]:
                changed_sources.add(source)
        if autopilot_changes_data:
            for source, changes in autopilot_changes_data[ad_group.campaign][ad_group].items():
                if changes["old_budget"] != changes["new_budget"]:
                    changed_sources.add(source)

    return changed_sources


def recalculate_budgets_campaign(campaign):
    if not campaign.settings.autopilot:
        bcm_modifiers = campaign.get_bcm_modifiers()
        budget_autopilot_adgroups = (
            campaign.adgroup_set.all()
            .filter(settings__autopilot_state=dash.constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET)
            .exclude_archived()
            .select_related("settings")
        )
        for ad_group in budget_autopilot_adgroups:
            _set_paused_ad_group_sources_to_minimum_values(ad_group, bcm_modifiers)

    run_autopilot(campaign=campaign, adjust_bids=False, adjust_budgets=True, initialization=True)


def _set_paused_ad_group_sources_to_minimum_values(ad_group, bcm_modifiers):
    all_rtb_ad_group_source = dash.models.AllRTBAdGroupSource(ad_group)
    ags_settings = helpers.get_autopilot_active_sources_settings(
        {ad_group: ad_group.settings}, dash.constants.AdGroupSettingsState.INACTIVE
    )
    if (
        ad_group.settings.b1_sources_group_enabled
        and ad_group.settings.b1_sources_group_state == dash.constants.AdGroupSourceSettingsState.INACTIVE
    ):
        ags_settings.append(all_rtb_ad_group_source)

    new_budgets = {}
    for ag_source_setting in ags_settings:
        if (
            ad_group.settings.b1_sources_group_enabled
            and ag_source_setting != all_rtb_ad_group_source
            and ag_source_setting.ad_group_source.source.source_type.type == dash.constants.SourceType.B1
        ):
            continue
        ag_source = (
            ag_source_setting.ad_group_source
            if ag_source_setting != all_rtb_ad_group_source
            else all_rtb_ad_group_source
        )
        old_budget = ad_group.settings.b1_sources_group_daily_budget
        if ag_source != all_rtb_ad_group_source:
            old_budget = (
                ag_source_setting.daily_budget_cc
                if ag_source_setting.daily_budget_cc
                else helpers.get_ad_group_sources_minimum_bid(ag_source, bcm_modifiers)
            )
        new_budgets[ag_source] = {
            "old_budget": old_budget,
            "new_budget": helpers.get_ad_group_sources_minimum_daily_budget(ag_source, bcm_modifiers),
            "budget_comments": [constants.DailyBudgetChangeComment.INITIALIZE_PILOT_PAUSED_SOURCE],
        }
    try:
        with transaction.atomic():
            set_autopilot_changes({}, new_budgets, ad_group)
            persist_autopilot_changes_to_log(
                ad_group, {}, new_budgets, new_budgets, dash.constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET
            )
    except Exception as e:
        _report_autopilot_exception(ags_settings, e)
    return new_budgets


def _get_autopilot_campaign_changes_data(ad_group, email_changes_data, bid_changes, budget_changes):
    camp = ad_group.campaign
    if camp not in email_changes_data:
        email_changes_data[camp] = {}
    email_changes_data[camp][ad_group] = {}
    for s in set(list(bid_changes.keys()) + list(budget_changes.keys())):
        email_changes_data[camp][ad_group][s] = {}
        if s in bid_changes:
            email_changes_data[camp][ad_group][s] = bid_changes[s].copy()
        if s in budget_changes:
            email_changes_data[camp][ad_group][s].update(budget_changes[s])
    return email_changes_data


def persist_autopilot_changes_to_log(
    ad_group,
    bid_changes,
    budget_changes,
    data,
    autopilot_state,
    campaign_goal_data=None,
    is_autopilot_job_run=False,
    campaign=None,
):
    rtb_as_one = ad_group.settings.b1_sources_group_enabled
    all_rtb_ad_group_source = dash.models.AllRTBAdGroupSource(ad_group)
    for ag_source in list(data.keys()):
        old_budget = data[ag_source]["old_budget"]
        goal_c = None
        if campaign_goal_data:
            goal_c = helpers.get_campaign_goal_column(campaign_goal_data["goal"])
        goal_value = data[ag_source][goal_c] if goal_c and goal_c in data[ag_source] else 0.0
        new_bid = data[ag_source].get("old_bid", None)
        if bid_changes:
            if ag_source in bid_changes:
                new_bid = bid_changes[ag_source]["new_bid"]
            elif rtb_as_one and all_rtb_ad_group_source in bid_changes:
                new_bid = bid_changes[all_rtb_ad_group_source]["new_bid"]
        new_daily_budget = old_budget
        if budget_changes:
            if ag_source in budget_changes:
                new_daily_budget = budget_changes[ag_source]["new_budget"]
            elif all_rtb_ad_group_source in budget_changes:
                new_daily_budget = None
        bid_comments = []
        if ag_source in bid_changes:
            bid_comments = bid_changes[ag_source]["bid_comments"]
        elif rtb_as_one and all_rtb_ad_group_source in bid_changes:
            bid_comments = bid_changes[all_rtb_ad_group_source]["bid_comments"]
        budget_comments = (
            budget_changes[ag_source]["budget_comments"] if budget_changes and ag_source in budget_changes else []
        )

        models.AutopilotLog(
            campaign=campaign,
            ad_group=ad_group,
            autopilot_type=autopilot_state,
            ad_group_source=ag_source if ag_source != all_rtb_ad_group_source else None,
            previous_cpc_cc=data[ag_source].get("old_bid", None),
            new_cpc_cc=new_bid,
            previous_daily_budget=old_budget,
            new_daily_budget=new_daily_budget,
            yesterdays_spend_cc=data[ag_source].get("yesterdays_spend_cc", None),
            yesterdays_clicks=data[ag_source].get("yesterdays_clicks", None),
            goal_value=goal_value,
            cpc_comments=", ".join(constants.BidChangeComment.get_text(c, ad_group.bidding_type) for c in bid_comments),
            budget_comments=", ".join(constants.DailyBudgetChangeComment.get_text(b) for b in budget_comments),
            campaign_goal=campaign_goal_data["goal"].type if campaign_goal_data else None,
            campaign_goal_optimal_value=campaign_goal_data["value"] if campaign_goal_data else None,
            is_autopilot_job_run=is_autopilot_job_run,
            is_rtb_as_one=rtb_as_one,
        ).save()


def set_autopilot_changes(
    bid_changes={}, budget_changes={}, ad_group=None, system_user=dash.constants.SystemUserType.AUTOPILOT, dry_run=False
):
    for ag_source in set(list(bid_changes.keys()) + list(budget_changes.keys())):
        changes = {}
        if (
            bid_changes
            and ag_source in bid_changes
            and bid_changes[ag_source]["old_bid"] != bid_changes[ag_source]["new_bid"]
        ):
            ad_group_source_bid_field = (
                "cpm" if ad_group and ad_group.bidding_type == dash.constants.BiddingType.CPM else "cpc_cc"
            )
            changes[ad_group_source_bid_field] = bid_changes[ag_source]["new_bid"]
        if (
            budget_changes
            and ag_source in budget_changes
            and budget_changes[ag_source]["old_budget"] != budget_changes[ag_source]["new_budget"]
        ):
            changes["daily_budget_cc"] = budget_changes[ag_source]["new_budget"]
        if changes and not dry_run:
            if ag_source.source == dash.models.AllRTBSource:
                helpers.update_ad_group_b1_sources_group_values(ad_group, changes, system_user)
            else:
                helpers.update_ad_group_source_values(ag_source, changes, system_user)


def _report_autopilot_exception(element, e):
    logger.exception(
        "Autopilot failed operating on {} because an exception was raised: {}".format(element, traceback.format_exc())
    )
    desc = {"element": ""}  # repr(element)
    pagerduty_helper.trigger(
        event_type=pagerduty_helper.PagerDutyEventType.ENGINEERS,
        incident_key="automation_autopilot_legacy_error",
        description="Autopilot failed operating on element because an exception was raised: {}".format(
            traceback.format_exc()
        ),
        details=desc,
    )


def _report_adgroups_data_to_influx(entities, campaign_daily_budgets):
    ad_group_ids = [ad_group.id for ad_groups_dict in entities.values() for ad_group in ad_groups_dict.keys()]
    num_campaigns_on_campaign_ap = 0
    num_ad_groups_on_campaign_ap = 0
    total_budget_on_campaign_ap = Decimal(0.0)
    num_on_budget_ap = 0
    total_budget_on_budget_ap = Decimal(0.0)
    num_on_bid_ap = 0
    yesterday_spend_on_bid_ap = Decimal(0.0)
    yesterday_spend_on_budget_ap = Decimal(0.0)
    yesterday_spend_on_campaign_ap = Decimal(0.0)
    yesterday = dates_helper.local_today() - datetime.timedelta(days=1)
    yesterday_data = redshiftapi.api_breakdowns.query(
        ["ad_group_id"],
        {"date__lte": yesterday, "date__gte": yesterday, "ad_group_id": ad_group_ids},
        parents=None,
        goals=None,
        use_publishers_view=False,
    )
    grouped_yesterday_data = {item["ad_group_id"]: item for item in yesterday_data}
    for campaign, ad_groups in entities.items():
        cost_key = "etfm_cost"
        if campaign.settings.autopilot:
            num_campaigns_on_campaign_ap += 1
            num_ad_groups_on_campaign_ap += len(ad_groups)
            yesterday_spend = Decimal(0.0)
            for ad_group in ad_groups:
                yesterday_spend += Decimal(grouped_yesterday_data.get(ad_group.id, {}).get(cost_key) or 0)
            yesterday_spend_on_campaign_ap += yesterday_spend
            total_budget_on_campaign_ap += campaign_daily_budgets[campaign]
        else:
            for ad_group in ad_groups:
                yesterday_spend = Decimal(grouped_yesterday_data.get(ad_group.id, {}).get(cost_key) or 0)
                if ad_group.settings.autopilot_state == dash.constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET:
                    num_on_budget_ap += 1
                    total_budget_on_budget_ap += ad_group.settings.autopilot_daily_budget
                    yesterday_spend_on_budget_ap += yesterday_spend
                elif ad_group.settings.autopilot_state == dash.constants.AdGroupSettingsAutopilotState.ACTIVE_CPC:
                    num_on_bid_ap += 1
                    yesterday_spend_on_bid_ap += yesterday_spend

    metrics_compat.gauge("automation.autopilot_plus_legacy.adgroups_on", num_on_budget_ap, autopilot="budget_autopilot")
    metrics_compat.gauge("automation.autopilot_plus_legacy.adgroups_on", num_on_bid_ap, autopilot="bid_autopilot")
    metrics_compat.gauge(
        "automation.autopilot_plus_legacy.adgroups_on", num_ad_groups_on_campaign_ap, autopilot="campaign_autopilot"
    )
    metrics_compat.gauge(
        "automation.autopilot_plus_legacy.campaigns_on", num_campaigns_on_campaign_ap, autopilot="campaign_autopilot"
    )

    metrics_compat.gauge(
        "automation.autopilot_plus_legacy.spend",
        total_budget_on_budget_ap,
        autopilot="budget_autopilot",
        type="expected",
    )
    metrics_compat.gauge(
        "automation.autopilot_plus_legacy.spend",
        total_budget_on_campaign_ap,
        autopilot="campaign_autopilot",
        type="expected",
    )

    metrics_compat.gauge(
        "automation.autopilot_plus_legacy.spend",
        yesterday_spend_on_campaign_ap,
        autopilot="campaign_autopilot",
        type="yesterday",
    )
    metrics_compat.gauge(
        "automation.autopilot_plus_legacy.spend",
        yesterday_spend_on_budget_ap,
        autopilot="budget_autopilot",
        type="yesterday",
    )
    metrics_compat.gauge(
        "automation.autopilot_plus_legacy.spend", yesterday_spend_on_bid_ap, autopilot="bid_autopilot", type="yesterday"
    )


def _report_new_budgets_on_ap_to_influx(entities):
    total_budget_on_campaign_ap = Decimal(0.0)
    total_budget_on_budget_ap = Decimal(0.0)
    total_budget_on_bid_ap = Decimal(0.0)
    total_budget_on_all_ap = Decimal(0.0)
    num_sources_on_campaign_ap = 0
    num_sources_on_budget_ap = 0
    num_sources_on_bid_ap = 0
    active = dash.constants.AdGroupSourceSettingsState.ACTIVE
    rtb_as_one_budget_counted_adgroups = set()
    for campaign, ad_groups in entities.items():
        for ad_group, ad_group_sources in ad_groups.items():
            for ad_group_source in ad_group_sources:
                daily_budget = ad_group_source.settings.daily_budget_cc or Decimal("0")
                if (
                    ad_group.settings.b1_sources_group_enabled
                    and ad_group.settings.b1_sources_group_state == active
                    and ad_group_source.source.source_type.type == dash.constants.SourceType.B1
                ):
                    if ad_group.id in rtb_as_one_budget_counted_adgroups:
                        continue
                    daily_budget = ad_group.settings.b1_sources_group_daily_budget or Decimal("0")
                    rtb_as_one_budget_counted_adgroups.add(ad_group.id)
                total_budget_on_all_ap += daily_budget
                if campaign.settings.autopilot:
                    total_budget_on_campaign_ap += daily_budget
                    num_sources_on_campaign_ap += 1
                elif (
                    ad_group.settings.autopilot_state == dash.constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET
                ):
                    total_budget_on_budget_ap += daily_budget
                    num_sources_on_budget_ap += 1
                elif ad_group.settings.autopilot_state == dash.constants.AdGroupSettingsAutopilotState.ACTIVE_CPC:
                    total_budget_on_bid_ap += daily_budget
                    num_sources_on_bid_ap += 1

    metrics_compat.gauge(
        "automation.autopilot_plus_legacy.spend", total_budget_on_bid_ap, autopilot="bid_autopilot", type="actual"
    )
    metrics_compat.gauge(
        "automation.autopilot_plus_legacy.spend", total_budget_on_budget_ap, autopilot="budget_autopilot", type="actual"
    )
    metrics_compat.gauge(
        "automation.autopilot_plus_legacy.spend",
        total_budget_on_campaign_ap,
        autopilot="campaign_autopilot",
        type="actual",
    )

    metrics_compat.gauge(
        "automation.autopilot_plus_legacy.sources_on", num_sources_on_bid_ap, autopilot="bid_autopilot"
    )
    metrics_compat.gauge(
        "automation.autopilot_plus_legacy.sources_on", num_sources_on_budget_ap, autopilot="budget_autopilot"
    )
    metrics_compat.gauge(
        "automation.autopilot_plus_legacy.sources_on", num_sources_on_campaign_ap, autopilot="campaign_autopilot"
    )


def adjust_ad_groups_flight_times_on_campaign_budget_autopilot_enabled(campaign):
    ad_groups = campaign.adgroup_set.all().exclude_archived().select_related("settings")
    for ad_group in ad_groups:
        _set_ad_group_flight_time_to_ongoing(ad_group)


def _set_ad_group_flight_time_to_ongoing(ad_group):
    today = dates_helper.local_today()
    updates = {"end_date": None}
    if ad_group.settings.start_date > today:
        updates["start_date"] = today

    ad_group.settings.update(
        None,
        skip_automation=True,
        system_user=dash.constants.SystemUserType.AUTOPILOT,
        skip_field_change_validation_autopilot=True,
        **updates,
    )
