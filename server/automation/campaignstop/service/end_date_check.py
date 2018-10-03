from django.db import transaction

import core.models

import core.features.bcm
from .. import constants
from .. import RealTimeCampaignStopLog, CampaignStopState
from utils import dates_helper


def update_campaigns_end_date(campaigns=None):
    if not campaigns:
        campaigns = core.models.Campaign.objects.filter(real_time_campaign_stop=True)

    _update_campaigns_end_date([campaign for campaign in campaigns if campaign.real_time_campaign_stop])


def _update_campaigns_end_date(campaigns):
    budgets_by_campaign = _prefetch_budgets(campaigns)
    for campaign in campaigns:
        _update_campaign_end_date(campaign, budgets_by_campaign.get(campaign.id, []))


@transaction.atomic
def _update_campaign_end_date(campaign, campaign_budgets):
    today = dates_helper.local_today()
    campaign_stop_state, _ = CampaignStopState.objects.get_or_create(campaign=campaign)
    log = RealTimeCampaignStopLog(campaign=campaign, event=constants.CampaignStopEvent.MAX_ALLOWED_END_DATE_UPDATE)
    campaign_stop_state.update_max_allowed_end_date(
        _calculate_max_allowed_end_date(log, campaign, campaign_budgets, today)
    )


def _prefetch_budgets(campaigns):
    # NOTE: taking all budgets into account (vs. only active/non-depleted) allows us
    # to consistently set end dates also for past campaigns. This way we avoid
    # changing end dates in external systems after they are over.
    budgets_by_campaign = {}
    for budget in (
        core.features.bcm.BudgetLineItem.objects.filter(campaign__in=campaigns)
        .order_by("start_date")
        .values("id", "campaign_id", "start_date", "end_date")
    ):
        budgets_by_campaign.setdefault(budget["campaign_id"], [])
        budgets_by_campaign[budget["campaign_id"]].append(budget)
    return budgets_by_campaign


def _calculate_max_allowed_end_date(log, campaign, campaign_budgets, current_date):
    campaign_created_date = dates_helper.utc_to_local(campaign.created_dt).date()
    max_allowed_end_date = dates_helper.day_before(campaign_created_date)
    for budget in campaign_budgets:
        if budget["start_date"] > current_date and budget["start_date"] > max_allowed_end_date:
            # NOTE: future non-overlapping budget; safe to stop
            break

        max_allowed_end_date = max(max_allowed_end_date, budget["end_date"])
    log.add_context({"budgets": campaign_budgets, "max_allowed_end_date": max_allowed_end_date})
    return max_allowed_end_date
