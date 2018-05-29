import decimal

import newrelic.agent

from . import refresh
from . import spends_helper
from .. import RealTimeCampaignStopLog
from ..constants import CampaignStopEvent


RESERVED_PROPORTION = decimal.Decimal('0.1')


class CampaignStopValidationException(Exception):
    def __init__(self, message, min_amount):
        super().__init__(message)
        self.min_amount = min_amount


@newrelic.agent.function_trace()
def validate_minimum_budget_amount(budget_line_item, amount):
    if not budget_line_item.campaign.real_time_campaign_stop:
        return

    log = RealTimeCampaignStopLog(
        campaign=budget_line_item.campaign, event=CampaignStopEvent.BUDGET_AMOUNT_VALIDATION)

    refresh.refresh_if_stale([budget_line_item.campaign])
    min_amount = _calculate_minimum_budget_amount(log, budget_line_item)
    log.add_context({
        'desired_amount': amount,
        'min_amount': min_amount,
    })
    if amount < min_amount:
        raise CampaignStopValidationException('Budget amount has to be at least ${}'.format(min_amount), min_amount)


def _calculate_minimum_budget_amount(log, budget_line_item):
    spend_estimates = spends_helper.get_budget_spend_estimates(log, budget_line_item.campaign)
    estimated_spend = spend_estimates.get(budget_line_item, 0)
    reserved_amount = estimated_spend * RESERVED_PROPORTION
    amount = estimated_spend + reserved_amount
    log.add_context({
        'spend_estimates': {budget.id: spend for budget, spend in spend_estimates.items()},
        'min_amount_raw': amount,
    })
    return _round(amount)


def _round(number):
    if number < 100:
        return _round_up_to_nearest(number, 10)
    return _round_up_to_nearest(number, 100)


def _round_up_to_nearest(number, multiple):
    return (int(number / multiple) + 1) * multiple
