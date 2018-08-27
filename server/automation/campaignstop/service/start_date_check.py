import core.bcm
import core.entity

from .. import CampaignStopState
from .. import RealTimeCampaignStopLog
from .. import constants
from . import config
from . import spends_helper

from utils import dates_helper


def update_campaigns_start_date(campaigns=None):
    if not campaigns:
        campaigns = core.entity.Campaign.objects.filter(real_time_campaign_stop=True)

    _update_campaigns_start_date(campaigns)


def _update_campaigns_start_date(campaigns):
    for campaign in campaigns:
        _update_campaign_start_date(campaign)


def _update_campaign_start_date(campaign):
    campaign_stop_state, _ = CampaignStopState.objects.get_or_create(campaign=campaign)
    min_start_date = _find_min_start_date(campaign)
    campaign_stop_state.update_min_allowed_start_date(min_start_date)


def _find_min_start_date(campaign):
    today = dates_helper.local_today()
    budgets = list(campaign.budgets.exclude(end_date__lt=today).order_by("start_date"))
    log = RealTimeCampaignStopLog(campaign=campaign, event=constants.CampaignStopEvent.MIN_ALLOWED_START_DATE_UPDATE)
    spend_estimates = spends_helper.get_budget_spend_estimates(log, campaign, budgets)
    for budget in budgets:
        if (
            sum(
                b.amount - spend_estimates.get(budget.id, 0)
                for b in _get_all_budgets_valid_on_date(budget.start_date, budgets)
            )
            > config.THRESHOLD
        ):
            return budget.start_date
    return None


def _get_all_budgets_valid_on_date(date, budgets):
    return (budget for budget in budgets if budget.start_date <= date and budget.end_date >= date)
