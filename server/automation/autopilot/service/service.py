import datetime
from collections import defaultdict
from decimal import Decimal

from django.db import transaction

import dash.constants
import dash.models
import etl.materialization_run
import redshiftapi.api_breakdowns
from automation import models
from utils import dates_helper
from utils import k1_helper
from utils import metrics_compat
from utils import slack
from utils import zlogging

from .. import constants
from . import budgets
from . import helpers
from . import prefetch
from .campaign import calculate_campaigns_daily_budget

logger = zlogging.getLogger(__name__)


@metrics_compat.timer("automation.autopilot_plus.run_autopilot")
def run_autopilot(campaign=None, adjust_budgets=True, update_metrics=False, dry_run=False, daily_run=False):
    processed_campaign_ids = None
    if daily_run:
        if not etl.materialization_run.etl_data_complete_for_date(dates_helper.local_yesterday()):
            logger.info("Autopilot daily run was aborted since materialized data is not yet available.")
            return

        processed_campaign_ids = helpers.get_processed_autopilot_campaign_ids(
            dates_helper.get_midnight(dates_helper.utc_now())
        )

        if processed_campaign_ids:
            logger.info("Excluding processed campaigns", num_excluded=len(processed_campaign_ids))

    entities = helpers.get_autopilot_entities(campaign=campaign, excluded_campaign_ids=processed_campaign_ids)
    campaign_daily_budgets = calculate_campaigns_daily_budget(campaign=campaign)

    data, campaign_goals, bcm_modifiers_map = prefetch.prefetch_autopilot_data(entities)
    if not data:
        return {}

    changes_data = defaultdict(dict)
    failed_campaigns = []

    for campaign, ad_groups in entities.items():
        try:
            ad_groups_data = _filter_ad_groups_data(data, ad_groups)
            budget_changes_map = _get_budget_predictions_for_campaign(
                campaign,
                campaign_daily_budgets[campaign],
                ad_groups_data,
                bcm_modifiers_map.get(campaign),
                campaign_goals.get(campaign, {}),
                adjust_budgets,
            )

            _update_autopilot_campaign_changes_data(changes_data, budget_changes_map)

            if not _save_changes(campaign, ad_groups_data, campaign_goals, budget_changes_map, dry_run, daily_run):
                failed_campaigns.append(campaign)

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

    if update_metrics:
        # refresh entities from db so we report new data, always report data for all entities
        entities = helpers.get_autopilot_entities()
        _update_autopilot_metrics(entities, campaign_daily_budgets)

    return changes_data


def _save_changes(campaign, ad_groups_data, campaign_goals, budget_changes_map, dry_run, daily_run):
    if dry_run:
        return True

    try:
        with transaction.atomic():
            for ad_group, data in ad_groups_data.items():
                budget_changes = budget_changes_map[ad_group]

                # TODO: RTAP: investigate daily_budget = 0 issue
                if not budget_changes["new_budget"]:
                    logger.info(
                        "Autopilot would update the ad group daily budget to zero",
                        campaign_id=campaign.id,
                        ad_group_id=ad_group.id,
                        budget_changes=budget_changes,
                    )
                    continue

                _set_autopilot_changes(ad_group, budget_changes, dry_run=dry_run)
                _persist_autopilot_changes_to_log(
                    campaign,
                    ad_group,
                    budget_changes,
                    data,
                    campaign_goals.get(campaign),
                    is_autopilot_job_run=daily_run,
                )

        for ad_group in ad_groups_data.keys():
            k1_helper.update_ad_group(ad_group, "run_autopilot")

    except Exception:
        logger.exception("Autopilot failed saving changes on autopilot campaign's ad groups", campaign_id=str(campaign))
        return False

    return True


def _filter_ad_groups_data(data, ad_groups):
    ad_groups_data = {}

    for ad_group in ad_groups:
        if ad_group not in data:
            logger.warning("Data for ad group not prefetched in AP", ad_group_id=str(ad_group))
            continue

        ad_groups_data[ad_group] = data[ad_group]

    return ad_groups_data


def _get_budget_predictions_for_campaign(
    campaign, daily_budget, ad_groups_data, bcm_modifiers, campaign_goal, adjust_budgets
):
    if not campaign.settings.autopilot:
        return {}
    if not adjust_budgets:
        return {}

    changes = budgets.get_autopilot_daily_budget_recommendations(
        campaign,
        daily_budget,
        ad_groups_data,
        bcm_modifiers,
        campaign_goal.get("goal"),
        ignore_daily_budget_too_small=True,
    )

    return changes


def recalculate_ad_group_budgets(campaign):
    if not campaign.settings.autopilot:
        return

    run_autopilot(campaign=campaign, adjust_budgets=True)


def _update_autopilot_campaign_changes_data(changes_data, budget_changes):
    for ad_group, changes in budget_changes.items():
        changes_data[ad_group.campaign][ad_group] = changes

    return changes_data


def _persist_autopilot_changes_to_log(
    campaign, ad_group, budget_changes, data, campaign_goal_data=None, is_autopilot_job_run=False
):
    yesterdays_spend = data.get("yesterdays_spend", None)
    old_budget = data["old_budget"]
    new_daily_budget = budget_changes["new_budget"] if budget_changes else old_budget
    budget_comments = budget_changes["budget_comments"] if budget_changes else []
    campaign_goal = campaign_goal_data["goal"].type if campaign_goal_data else None
    campaign_goal_optimal_value = campaign_goal_data["value"] if campaign_goal_data else None
    goal_column = helpers.get_campaign_goal_column(campaign_goal_data["goal"]) if campaign_goal_data else None
    goal_value = data[goal_column] if goal_column and goal_column in data else 0.0

    models.AutopilotLog(
        campaign=campaign,
        ad_group=ad_group,
        yesterdays_spend_cc=yesterdays_spend,
        previous_daily_budget=old_budget,
        new_daily_budget=new_daily_budget,
        budget_comments=", ".join(constants.DailyBudgetChangeComment.get_text(b) for b in budget_comments),
        campaign_goal=campaign_goal,
        campaign_goal_optimal_value=campaign_goal_optimal_value,
        goal_value=goal_value,
        is_autopilot_job_run=is_autopilot_job_run,
    ).save()


def _set_autopilot_changes(ad_group, budget_changes, dry_run=False):
    if dry_run:
        return

    if budget_changes and budget_changes["old_budget"] != budget_changes["new_budget"]:
        helpers.update_ad_group_daily_budget(ad_group, budget_changes["new_budget"])


def _update_autopilot_metrics(entities, campaign_daily_budgets):
    ad_group_ids = [ad_group.id for ad_groups_list in entities.values() for ad_group in ad_groups_list]

    num_campaigns = 0
    num_ad_groups = 0
    total_budget_expected = Decimal(0.0)
    total_budget_actual = Decimal(0.0)
    yesterday_spend = Decimal(0.0)

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
        num_campaigns += 1
        num_ad_groups += len(ad_groups)
        total_budget_expected += campaign_daily_budgets[campaign]

        for ad_group in ad_groups:
            total_budget_actual += ad_group.settings.daily_budget or Decimal("0")
            yesterday_spend += Decimal(grouped_yesterday_data.get(ad_group.id, {}).get("etfm_cost") or 0)

    metrics_compat.gauge("automation.autopilot_plus.adgroups_on", num_ad_groups, autopilot="campaign_autopilot")
    metrics_compat.gauge("automation.autopilot_plus.campaigns_on", num_campaigns, autopilot="campaign_autopilot")
    metrics_compat.gauge(
        "automation.autopilot_plus.spend", total_budget_expected, autopilot="campaign_autopilot", type="expected"
    )
    metrics_compat.gauge(
        "automation.autopilot_plus.spend", total_budget_actual, autopilot="campaign_autopilot", type="actual"
    )
    metrics_compat.gauge(
        "automation.autopilot_plus.spend", yesterday_spend, autopilot="campaign_autopilot", type="yesterday"
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
        **updates
    )
