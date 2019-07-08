import decimal

import newrelic.agent

import core.features.bcm
from utils import dates_helper

from . import refresh
from . import spends_helper
from .. import RealTimeCampaignStopLog
from ..constants import CampaignStopEvent

RESERVED_PROPORTION = decimal.Decimal("0.1")


class CampaignStopValidationException(Exception):
    def __init__(self, message, min_amount):
        super().__init__(message)
        self.min_amount = min_amount


@newrelic.agent.function_trace()
def validate_minimum_budget_amount(budget_line_item, amount):
    if not budget_line_item.campaign.real_time_campaign_stop:
        return

    log = RealTimeCampaignStopLog(campaign=budget_line_item.campaign, event=CampaignStopEvent.BUDGET_AMOUNT_VALIDATION)

    refresh.refresh_if_stale([budget_line_item.campaign])
    min_amount = _calculate_minimum_budget_amount(log, budget_line_item)
    log.add_context({"desired_amount": amount, "min_amount": min_amount})
    if amount < min_amount:
        raise CampaignStopValidationException("Budget amount has to be at least ${}".format(min_amount), min_amount)


def _calculate_minimum_budget_amount(log, budget_line_item):
    budgets_active_today = _get_budgets_active_today(budget_line_item.campaign)
    spend_estimates = spends_helper.get_budget_spend_estimates(log, budget_line_item.campaign, budgets_active_today)
    estimated_spend = spend_estimates.get(budget_line_item, 0)
    reserved_amount = estimated_spend * RESERVED_PROPORTION
    amount = estimated_spend + reserved_amount
    log.add_context(
        {"spend_estimates": {budget.id: spend for budget, spend in spend_estimates.items()}, "min_amount_raw": amount}
    )
    rounded_amount = _round(amount)
    prev_amount = core.features.bcm.BudgetLineItem.objects.filter(id=budget_line_item.id).values_list(
        "amount", flat=True
    )[0]
    return min(rounded_amount, prev_amount)  # even if the calculation is off increasing the amount should be safe


def _get_budgets_active_today(campaign):
    today = dates_helper.local_today()
    return campaign.budgets.filter(start_date__lte=today, end_date__gte=today).order_by("created_dt")


def _round(number):
    if number == 0:
        return 0

    if number < 100:
        return _round_up_to_nearest(number, 10)
    return _round_up_to_nearest(number, 100)


def _round_up_to_nearest(number, multiple):
    return (int(number / multiple) + 1) * multiple
