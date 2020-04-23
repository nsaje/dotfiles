from typing import Any
from typing import Dict
from typing import Sequence

import core.models
from utils import dates_helper

from ... import constants
from . import helpers


def prepare_budgets(ad_groups: Sequence[core.models.AdGroup]) -> Dict[int, Dict[str, Any]]:
    local_today = dates_helper.local_today()  # NOTE: using local today since budget dates are in local timezone
    campaigns = core.models.Campaign.objects.filter(adgroup__in=ad_groups)
    budgets_by_campaign_id = _fetch_bugets(campaigns)

    budgets_data_by_campaign_id = {}
    for campaign in core.models.Campaign.objects.filter(adgroup__in=ad_groups):
        if campaign.id not in budgets_by_campaign_id:
            continue
        campaign_budgets = budgets_by_campaign_id[campaign.id]
        (start_date, end_date, remaining_budget, margin) = _calculate_budget_data_for_campaign(
            campaign, campaign_budgets
        )
        budgets_data_by_campaign_id[campaign.id] = helpers.map_keys_from_constant_to_qs_string_representation(
            {
                constants.MetricType.CAMPAIGN_BUDGET_START_DATE: start_date,
                constants.MetricType.DAYS_SINCE_CAMPAIGN_BUDGET_START: (local_today - start_date).days,
                constants.MetricType.CAMPAIGN_BUDGET_END_DATE: end_date,
                constants.MetricType.DAYS_UNTIL_CAMPAIGN_BUDGET_END: (end_date - local_today).days,
                constants.MetricType.CAMPAIGN_REMAINING_BUDGET: remaining_budget,
                constants.MetricType.CAMPAIGN_BUDGET_MARGIN: margin,
            }
        )

    return budgets_data_by_campaign_id


def _fetch_bugets(campaigns):
    budgets_by_campaign_id = {}
    for budget in core.features.bcm.BudgetLineItem.objects.filter(campaign__in=campaigns):
        budgets_by_campaign_id.setdefault(budget.campaign_id, [])
        budgets_by_campaign_id[budget.campaign_id].append(budget)
    return budgets_by_campaign_id


def _calculate_budget_data_for_campaign(campaign, campaign_budgets):
    campaign_budgets = sorted(campaign_budgets, key=lambda x: x.start_date)
    min_start_date = _find_min_start_date(campaign_budgets)
    max_end_date = _find_max_end_date(campaign_budgets)
    budgets_active_today = _filter_budgets_active_today(campaign_budgets)
    margin = (
        budgets_active_today[0].margin if budgets_active_today else None
    )  # NOTE: assumes margin is the same for all budgets active on a single day
    remaining_budget = sum(max(bli.get_available_etfm_amount(), 0) for bli in budgets_active_today)
    return min_start_date, max_end_date, remaining_budget, margin


def _find_min_start_date(campaign_budgets):
    campaign_budgets = sorted(campaign_budgets, key=lambda x: x.end_date, reverse=True)
    min_start_date = None
    for budget in campaign_budgets:
        if budget.end_date < dates_helper.local_today() and (not min_start_date or budget.end_date < min_start_date):
            # NOTE: past non-overlapping budgets are not relevant
            break

        min_start_date = min(min_start_date, budget.start_date) if min_start_date else budget.start_date
    return min_start_date


def _find_max_end_date(campaign_budgets):
    campaign_budgets = sorted(campaign_budgets, key=lambda x: x.start_date)
    max_end_date = None
    for budget in campaign_budgets:
        if budget.start_date > dates_helper.local_today() and (not max_end_date or budget.start_date > max_end_date):
            # NOTE: future non-overlapping budgets are not relevant
            break

        max_end_date = max(max_end_date, budget.end_date) if max_end_date else budget.end_date
    return max_end_date


def _filter_budgets_active_today(campaign_budgets):
    local_today = dates_helper.local_today()
    budgets_active_today = []
    for budget in campaign_budgets:
        if budget.start_date <= local_today and budget.end_date >= local_today:
            budgets_active_today.append(budget)
    return budgets_active_today
