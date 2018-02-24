import decimal

from django.core.exceptions import ValidationError

from .import campaign_spends
from .. import RealTimeCampaignStopLog
from ..constants import CampaignStopEvent

RESERVED_PROPORTION = decimal.Decimal('0.1')


class CampaignStopValidationError(ValidationError):
    pass


def validate_minimum_budget_amount(budget_line_item, amount):
    if not budget_line_item.campaign.real_time_campaign_stop:
        return

    log = RealTimeCampaignStopLog(
        campaign=budget_line_item.campaign, event=CampaignStopEvent.BUDGET_AMOUNT_VALIDATION)

    min_amount = _calculate_minimum_budget_amount(log, budget_line_item)
    if amount < min_amount:
        raise CampaignStopValidationError(
            'Budget amount has to be at least ${}'.format(min_amount))


def _calculate_minimum_budget_amount(log, budget_line_item):
    spend_estimates = campaign_spends.get_budget_spend_estimates(log, budget_line_item.campaign)
    estimated_spend = spend_estimates.get(budget_line_item, 0)
    reserved_amount = estimated_spend * RESERVED_PROPORTION
    return _round(estimated_spend + reserved_amount)


def _round(number):
    if number < 100:
        return _round_to_nearest(number, 10)
    return _round_to_nearest(number, 100)


def _round_to_nearest(number, multiple):
    return (int(number / multiple) + 1) * multiple
