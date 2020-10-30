import datetime
from collections import defaultdict
from decimal import Decimal

import dash.campaign_goals
import dash.constants
import dash.models
import redshiftapi.api_breakdowns
from stats.api_breakdowns import Goals
from utils import dates_helper

from .. import settings
from . import helpers


def prefetch_autopilot_data(entities):
    campaigns = entities.keys()
    campaign_goals, conversion_goals, pixels = _get_autopilot_goals(campaigns)
    yesterday_data, days_ago_data, conv_days_ago_data = _fetch_redshift_data(entities, conversion_goals, pixels)
    bcm_modifiers_map = _get_bcm_modifiers(campaigns)

    data = {}
    for campaign, ad_groups in entities.items():
        campaign_goal_data = campaign_goals.get(campaign)
        goal_col = helpers.get_campaign_goal_column(campaign_goal_data["goal"]) if campaign_goal_data else None
        goal_optimal = campaign_goal_data["value"] if campaign_goal_data else None

        for ad_group in ad_groups:
            ad_group_data = _init_ad_group_data(
                ad_group.settings, yesterday_data.get(ad_group.id, {}), goal_col, goal_optimal
            )
            ad_group_goal_data = _init_ad_group_goal_data(
                days_ago_data.get(ad_group.id, {}),
                conv_days_ago_data.get(ad_group.id, {}),
                conversion_goals,
                campaign_goal_data,
                goal_col,
                goal_optimal,
            )
            data[ad_group] = {**ad_group_data, **ad_group_goal_data}

    return data, campaign_goals, bcm_modifiers_map


def _get_autopilot_goals(campaigns):
    campaign_goals = {}
    conversion_goals = []
    pixels = []
    campaigns_map = {campaign.id: campaign for campaign in campaigns}
    primary_goal_values = dash.campaign_goals.get_campaigns_goal_values(campaigns).filter(campaign_goal__primary=True)
    for primary_goal_value in primary_goal_values:
        primary_goal = primary_goal_value.campaign_goal
        value = primary_goal_value.value
        if primary_goal.type == dash.constants.CampaignGoalKPI.CPA and value:
            value = Decimal("1.0") / value
        campaign_goals[campaigns_map[primary_goal.campaign_id]] = {"goal": primary_goal, "value": value}
        if primary_goal and primary_goal.type == dash.constants.CampaignGoalKPI.CPA:
            conversion_goals.append(primary_goal.conversion_goal)
            if primary_goal.conversion_goal.type == dash.constants.ConversionGoalType.PIXEL:
                pixels.append(primary_goal.conversion_goal.pixel)
    return campaign_goals, conversion_goals, pixels


def _fetch_redshift_data(entities, conversion_goals, pixels):
    today = dates_helper.local_today()
    yesterday = today - datetime.timedelta(days=1)
    days_ago = yesterday - datetime.timedelta(days=settings.AUTOPILOT_DATA_LOOKBACK_DAYS)
    conversion_data_days_ago = yesterday - datetime.timedelta(days=settings.AUTOPILOT_CONVERSION_DATA_LOOKBACK_DAYS)
    ad_group_ids = [ad_group.id for ad_groups_list in entities.values() for ad_group in ad_groups_list]

    yesterday_data = redshiftapi.api_breakdowns.query(
        ["ad_group_id"],
        {"date__gte": yesterday, "date__lte": yesterday, "ad_group_id": ad_group_ids},
        parents=None,
        goals=None,
        use_publishers_view=False,
    )

    days_ago_data = redshiftapi.api_breakdowns.query(
        ["ad_group_id"],
        {"date__gte": days_ago, "date__lte": yesterday, "ad_group_id": ad_group_ids},
        parents=None,
        goals=None,
        use_publishers_view=False,
    )

    stats_goals = Goals(
        conversion_goals=conversion_goals,
        pixels=pixels,
        # NOTE: campaign goals are handled separately
        campaign_goals=[],
        campaign_goal_values=[],
        primary_goals=[],
    )
    conversions_days_ago_data = redshiftapi.api_breakdowns.query(
        ["ad_group_id"],
        {"date__gte": conversion_data_days_ago, "date__lte": yesterday, "ad_group_id": ad_group_ids},
        parents=None,
        goals=stats_goals,
        use_publishers_view=False,
    )

    return (
        _group_redshift_data(yesterday_data),
        _group_redshift_data(days_ago_data),
        _group_redshift_data(conversions_days_ago_data),
    )


def _group_redshift_data(data):
    grouped_data = defaultdict(dict)
    for item in data:
        grouped_data[item["ad_group_id"]] = item
    return grouped_data


def _get_bcm_modifiers(campaigns):
    # NOTE: Modifiers are only fetched for ad groups' campaigns that have
    # budgets assuming ad groups without budgets aren't running and aren't
    # handled by autopilot because of that.
    campaign_budgets = {
        budget.campaign_id: budget
        for budget in dash.models.BudgetLineItem.objects.filter(campaign__in=campaigns)
        .filter_today()
        .distinct("campaign_id")
        .select_related("credit")
    }

    bcm_modifiers = {}
    for campaign in campaigns:
        if campaign.id in campaign_budgets:
            budget = campaign_budgets[campaign.id]
            bcm_modifiers[campaign] = {
                "service_fee": budget.credit.service_fee,
                "fee": budget.credit.license_fee,
                "margin": budget.margin,
            }
    return bcm_modifiers


def _init_ad_group_data(adg_settings, yesterday_row, goal_col, goal_optimal):
    yesterdays_spend = Decimal(yesterday_row.get("etfm_cost") or 0)
    return {
        "old_budget": adg_settings.daily_budget,
        "yesterdays_spend": yesterdays_spend,
        "spend_perc": yesterdays_spend / adg_settings.daily_budget,
    }


def _init_ad_group_goal_data(
    days_ago_row, conv_days_ago_row, conversion_goals, campaign_goal_data, goal_col, goal_optimal
):
    dividend, divisor = _populate_prefetch_adgroup_goal_data(
        campaign_goal_data, goal_col, conv_days_ago_row, conversion_goals, days_ago_row
    )
    goal_value = (
        dividend / divisor if dividend and divisor and divisor > 0.0 else settings.GOALS_WORST_VALUE.get(goal_col)
    )
    goal_performance = 0.0

    if goal_optimal and goal_value and goal_optimal > 0.0 and goal_value > 0.0:
        goal_high_is_good = (
            campaign_goal_data and settings.GOALS_CALC_COLS[campaign_goal_data["goal"].type]["high_is_good"]
        )
        if goal_high_is_good:
            goal_performance = min(float(goal_value) / float(goal_optimal), 1.0)
        else:
            goal_performance = min(float(goal_optimal) / float(goal_value), 1.0)

    return {
        goal_col: goal_value,
        "goal_optimal": goal_optimal,
        "dividend": dividend,
        "divisor": divisor,
        "goal_performance": goal_performance,
    }


def _populate_prefetch_adgroup_goal_data(campaign_goal_data, goal_col, conv_days_ago_row, conv_goals, days_ago_row):
    if not campaign_goal_data:
        return None, None

    if campaign_goal_data["goal"].type == dash.constants.CampaignGoalKPI.CPA:
        return _get_conversions_per_cost_value(
            conv_days_ago_row, campaign_goal_data["goal"].conversion_goal, conv_goals
        )

    elif goal_col in days_ago_row and days_ago_row[goal_col]:
        return _get_other_goal_cost_value(days_ago_row, campaign_goal_data["goal"])

    return None, None


def _get_conversions_per_cost_value(conv_days_ago_row, conversion_goal, conversion_goals):
    view_key = conversion_goal.get_view_key(conversion_goals)
    spend = float(conv_days_ago_row.get("etfm_cost") or 0)
    conv = conv_days_ago_row.get(view_key)

    return conv, spend


def _get_other_goal_cost_value(days_ago_row, goal):
    goal_calculation_definition = settings.GOALS_CALC_COLS[goal.type]
    dividend_column = goal_calculation_definition["dividend"]
    divisor_column = goal_calculation_definition["divisor"]

    dividend = float(days_ago_row[dividend_column])
    divisor = float(days_ago_row[divisor_column])

    return dividend, divisor
