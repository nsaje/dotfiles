import decimal

from django.db import transaction

import core.entity
from utils import dates_helper

from . import campaign_spends
from .. import CampaignStopState
from .. import constants
from .. import RealTimeCampaignStopLog

THRESHOLD = decimal.Decimal('10')
HOURS_DELAY = 6


def update_campaigns_state(campaigns=None):
    if not campaigns:
        campaigns = core.entity.Campaign.objects.filter(real_time_campaign_stop=True)
    _update_campaigns(campaign for campaign in campaigns if campaign.real_time_campaign_stop)


def _update_campaigns(campaigns):
    for campaign in campaigns:
        _update_campaign(campaign)


@transaction.atomic
def _update_campaign(campaign):
    campaign_state, _ = CampaignStopState.objects.get_or_create(campaign=campaign)

    log = RealTimeCampaignStopLog(
        campaign=campaign, event=constants.CampaignStopEvent.BUDGET_DEPLETION_CHECK)

    log.add_context({'previous_state': campaign_state.state})
    campaign_state.set_allowed_to_run(_is_allowed_to_run(log, campaign, campaign_state))
    log.add_context({'new_state': campaign_state.state})


def _is_allowed_to_run(log, campaign, campaign_state):
    allowed_to_run = (
        not _is_max_end_date_past(log, campaign, campaign_state) and
        not _is_below_threshold(log, campaign)
    )
    log.add_context({'allowed_to_run': allowed_to_run})
    return allowed_to_run


def _is_max_end_date_past(log, campaign, campaign_state):
    is_past = (
        campaign_state.max_allowed_end_date and
        campaign_state.max_allowed_end_date < dates_helper.local_today()
    )
    log.add_context({
        'max_allowed_end_date': campaign_state.max_allowed_end_date,
        'is_max_end_date_past': is_past,
    })
    return is_past


def _is_below_threshold(log, campaign):
    predicted = campaign_spends.get_predicted_remaining_budget(log, campaign)
    is_below = predicted < THRESHOLD
    log.add_context({
        'predicted': predicted,
        'is_below_threshold': is_below,
        'threshold': THRESHOLD,
    })
    return is_below
