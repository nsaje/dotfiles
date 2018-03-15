from collections import defaultdict
import datetime
from decimal import Decimal

import dash.campaign_goals
import dash.constants
import dash.models
import redshiftapi.api_breakdowns
from stats.api_breakdowns import Goals
from utils import dates_helper

from . import helpers
from . import settings


def prefetch_autopilot_data(entities):
    campaigns = entities.keys()
    campaign_goals, conversion_goals, pixels = _get_autopilot_goals(campaigns)
    yesterday_data, days_ago_data, conv_days_ago_data = _fetch_redshift_data(entities, conversion_goals, pixels)
    bcm_modifiers_map = _get_bcm_modifiers(campaigns)

    data = {}
    for campaign, ad_groups_dict in entities.items():
        bcm_modifiers = bcm_modifiers_map.get(campaign)

        campaign_goal_data = campaign_goals.get(campaign)
        goal_col, goal_optimal = None, None
        if campaign_goal_data:
            goal_col = helpers.get_campaign_goal_column(
                campaign_goal_data['goal'],
                campaign.account.uses_bcm_v2,
            )
            goal_optimal = campaign_goal_data['value']

        for ad_group, ad_group_sources in ad_groups_dict.items():
            source_all_rtb_active = (
                ad_group.settings.b1_sources_group_enabled and
                ad_group.settings.b1_sources_group_state == dash.constants.AdGroupSourceSettingsState.ACTIVE)

            data[ad_group] = {}
            # TODO: change constant for something per ad_group different
            if source_all_rtb_active:
                data[ad_group][dash.constants.SourceAllRTB] = _init_b1_sources_data(ad_group.settings, goal_col, goal_optimal)

            for ad_group_source in ad_group_sources:

                data[ad_group][ad_group_source] = _populate_prefetch_adgroup_source_data(
                    ad_group_source,
                    yesterday_data[ad_group.id].get(ad_group_source.source_id, {}),
                    bcm_modifiers,
                    uses_bcm_v2=campaign.account.uses_bcm_v2,
                )

                if campaign_goal_data:
                    data[ad_group][ad_group_source].update(_populate_prefetch_adgroup_source_goal_data(
                        goal_col, goal_optimal, campaign_goal_data,
                        conv_days_ago_data[ad_group.id].get(ad_group_source.source_id, {}),
                        conversion_goals,
                        days_ago_data[ad_group.id].get(ad_group_source.source_id, {}),
                        settings.GOALS_CALC_COLS[campaign_goal_data['goal'].type]['high_is_good'],
                        uses_bcm_v2=campaign.account.uses_bcm_v2,
                    ))

                if source_all_rtb_active and ad_group_source.source.source_type.type == dash.constants.SourceType.B1:
                    data[ad_group][dash.constants.SourceAllRTB] = _populate_b1_sources_data(
                        data[ad_group][ad_group_source],
                        data[ad_group][dash.constants.SourceAllRTB],
                        goal_col, goal_optimal,
                        settings.GOALS_CALC_COLS[campaign_goal_data['goal'].type]['high_is_good'] if campaign_goal_data else None,
                    )

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
            value = Decimal('1.0') / value
        campaign_goals[campaigns_map[primary_goal.campaign_id]] = {'goal': primary_goal, 'value': value}
        if primary_goal and primary_goal.type == dash.constants.CampaignGoalKPI.CPA:
            conversion_goals.append(primary_goal.conversion_goal)
            if primary_goal.conversion_goal.type == dash.constants.ConversionGoalType.PIXEL:
                pixels.append(primary_goal.conversion_goal.pixel)
    return campaign_goals, conversion_goals, pixels


def _fetch_redshift_data(entities, conversion_goals, pixels):
    today = dates_helper.local_today()
    yesterday = today - datetime.timedelta(days=1)
    days_ago = yesterday - datetime.timedelta(days=settings.AUTOPILOT_DATA_LOOKBACK_DAYS)
    conversion_data_days_ago = yesterday - datetime.timedelta(
        days=settings.AUTOPILOT_CONVERSION_DATA_LOOKBACK_DAYS)
    ad_group_ids = [ad_group.id for ad_groups_dict in entities.values() for ad_group in ad_groups_dict.keys()]

    yesterday_data = redshiftapi.api_breakdowns.query(
        ['ad_group_id', 'source_id'],
        {
            'date__gte': yesterday,
            'date__lte': yesterday,
            'ad_group_id': ad_group_ids,
        },
        parents=None,
        goals=None,
        use_publishers_view=False,
    )

    days_ago_data = redshiftapi.api_breakdowns.query(
        ['ad_group_id', 'source_id'],
        {
            'date__gte': days_ago,
            'date__lte': yesterday,
            'ad_group_id': ad_group_ids,
        },
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
        primary_goals=[]
    )
    conversions_days_ago_data = redshiftapi.api_breakdowns.query(
        ['ad_group_id', 'source_id'],
        {
            'date__gte': conversion_data_days_ago,
            'date__lte': yesterday,
            'ad_group_id': ad_group_ids,
        },
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
        grouped_data[item['ad_group_id']][item['source_id']] = item
    return grouped_data


def _get_bcm_modifiers(campaigns):
    # NOTE: Modifiers are only fetched for ad groups' campaigns that have
    # budgets assuming ad groups without budgets aren't running and aren't
    # handled by autopilot because of that.
    campaign_budgets = {
        budget.campaign_id: budget for budget in dash.models.BudgetLineItem.objects.filter(
            campaign__in=campaigns,
        ).filter_today().distinct('campaign_id').select_related('credit')
    }

    bcm_modifiers = {}
    for campaign in campaigns:
        if campaign.account.uses_bcm_v2 and campaign.id in campaign_budgets:
            budget = campaign_budgets[campaign.id]
            bcm_modifiers[campaign] = {
                'fee': budget.credit.license_fee,
                'margin': budget.margin,
            }
    return bcm_modifiers


def _init_b1_sources_data(adg_settings, goal_col, goal_optimal):
    return {
        goal_col: None,
        'yesterdays_clicks': 0,
        'old_budget': adg_settings.b1_sources_group_daily_budget,
        'old_cpc_cc': adg_settings.b1_sources_group_cpc_cc,
        'yesterdays_spend_cc': Decimal('0.0'),
        'spend_perc': Decimal('0.0'),
        'dividend': None,
        'divisor': None,
        'goal_optimal': goal_optimal,
        'goal_performance': 0.0,
    }


def _populate_b1_sources_data(row, current_b1_data, goal_col, goal_optimal, goal_high_is_good):
    current_b1_data['yesterdays_clicks'] += row['yesterdays_clicks']
    current_b1_data['yesterdays_spend_cc'] += row['yesterdays_spend_cc']
    current_b1_data['spend_perc'] = current_b1_data['yesterdays_spend_cc'] / current_b1_data['old_budget']
    if row.get('dividend'):
        current_b1_data['dividend'] = row['dividend'] + (current_b1_data['dividend'] or 0.0)
    if row.get('divisor'):
        current_b1_data['divisor'] = row['divisor'] + (current_b1_data['divisor'] or 0.0)
    current_b1_data[goal_col] = current_b1_data['dividend'] / current_b1_data['divisor'] if\
        current_b1_data['dividend'] and current_b1_data['divisor'] and current_b1_data['divisor'] > 0.0 else\
        settings.GOALS_WORST_VALUE.get(goal_col)
    current_b1_data['goal_optimal'] = goal_optimal

    if (current_b1_data['goal_optimal'] and current_b1_data[goal_col] and
            current_b1_data['goal_optimal'] > 0.0 and current_b1_data[goal_col] > 0.0):
        if goal_high_is_good:
            current_b1_data['goal_performance'] = min(float(current_b1_data[goal_col]) /
                                                      float(current_b1_data['goal_optimal']), 1.0)
        else:
            current_b1_data['goal_performance'] = min(float(current_b1_data['goal_optimal']) /
                                                      float(current_b1_data[goal_col]), 1.0)

    return current_b1_data


def _populate_prefetch_adgroup_source_data(ad_group_source, yesterday_row, bcm_modifiers, uses_bcm_v2=False):
    spend_key = 'etfm_cost' if uses_bcm_v2 else 'et_cost'

    data = {}
    budget = ad_group_source.settings.daily_budget_cc if ad_group_source.settings.daily_budget_cc else\
        ad_group_source.source.source_type.get_etfm_min_daily_budget(bcm_modifiers)
    data['yesterdays_spend_cc'] = Decimal(yesterday_row.get(spend_key) or 0)
    data['yesterdays_clicks'] = yesterday_row.get('clicks') or 0
    data['old_budget'] = budget or 0
    data['old_cpc_cc'] = ad_group_source.settings.cpc_cc if ad_group_source.settings.cpc_cc else\
        ad_group_source.source.default_cpc_cc
    data['spend_perc'] = data['yesterdays_spend_cc'] / budget
    return data


def _populate_prefetch_adgroup_source_goal_data(
        goal_col, goal_optimal, campaign_goal_data, conv_days_ago_row, conv_goals, row, goal_high_is_good, uses_bcm_v2=False):
    goal_value = settings.GOALS_WORST_VALUE.get(goal_col)
    dividend = None
    divisor = None
    goal_performance = 0.0
    if campaign_goal_data['goal'].type == dash.constants.CampaignGoalKPI.CPA:
        dividend, divisor, goal_value = _get_conversions_per_cost_value(
            conv_days_ago_row, campaign_goal_data['goal'].conversion_goal, conv_goals, uses_bcm_v2=uses_bcm_v2)
    elif goal_col in row and row[goal_col]:
        dividend, divisor, goal_value = _get_other_goal_cost_value(
            row, campaign_goal_data['goal'], goal_col, uses_bcm_v2=uses_bcm_v2)

    if goal_optimal and goal_value and goal_optimal > 0.0 and goal_value > 0.0:
        goal_performance = (min(float(goal_value) / float(goal_optimal), 1.0) if goal_high_is_good else
                            min(float(goal_optimal) / float(goal_value), 1.0))

    return {
        goal_col: goal_value,
        'dividend': dividend,
        'divisor': divisor,
        'goal_optimal': goal_optimal,
        'goal_performance': goal_performance,
    }


def _get_conversions_per_cost_value(row, conversion_goal, conversion_goals, uses_bcm_v2=False):
    view_key = conversion_goal.get_view_key(conversion_goals)
    if uses_bcm_v2:
        spend = float(row.get('etfm_cost') or 0)
    else:
        spend = float(row.get('et_cost') or 0)
    conv = row.get(view_key)
    return conv, spend, ((conv or 0.0) / spend) if spend > 0 else 0.0


def _get_other_goal_cost_value(row, goal, goal_col, uses_bcm_v2=False):
    goal_calculation_definition = settings.GOALS_CALC_COLS[goal.type]
    dividend_column = goal_calculation_definition['dividend']
    if uses_bcm_v2 and\
       'dividend_bcm_v2' in goal_calculation_definition:
        dividend_column = goal_calculation_definition['dividend_bcm_v2']

    divisor_column = goal_calculation_definition['divisor']
    if uses_bcm_v2 and\
       'divisor_bcm_v2' in goal_calculation_definition:
        divisor_column = goal_calculation_definition['divisor_bcm_v2']

    dividend = float(row[dividend_column])
    divisor = float(row[divisor_column])
    goal_value = row[goal_col]
    return dividend, divisor, goal_value
