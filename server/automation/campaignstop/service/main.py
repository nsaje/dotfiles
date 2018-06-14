import decimal

from django.db import transaction

import core.entity
from utils import dates_helper

from . import spends_helper
from . import refresh_realtime_data
from .. import CampaignStopState
from .. import constants
from .. import RealTimeCampaignStopLog

THRESHOLD = decimal.Decimal('10')


def update_campaigns_state(campaigns=None):
    if not campaigns:
        campaigns = core.entity.Campaign.objects.filter(real_time_campaign_stop=True)
    _update_campaigns(campaign for campaign in campaigns if campaign.real_time_campaign_stop)


def _update_campaigns(campaigns):
    for campaign in campaigns:
        refresh_realtime_data([campaign])
        _update_campaign(campaign)


@transaction.atomic
def _update_campaign(campaign):
    campaign_state, _ = CampaignStopState.objects.get_or_create(campaign=campaign)

    log = RealTimeCampaignStopLog(
        campaign=campaign, event=constants.CampaignStopEvent.BUDGET_DEPLETION_CHECK)

    log.add_context({'previous_state': campaign_state.state})
    allowed_to_run = _is_allowed_to_run(log, campaign, campaign_state)
    campaign_state.set_allowed_to_run(allowed_to_run)
    if not allowed_to_run:
        campaign_state.update_almost_depleted(False)
    log.add_context({'new_state': campaign_state.state})


def _is_allowed_to_run(log, campaign, campaign_state):
    allowed_to_run = (
        not _is_max_end_date_past(log, campaign, campaign_state) and
        not _is_below_threshold(log, campaign, campaign_state)
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


def _is_below_threshold(log, campaign, campaign_state):
    predicted = spends_helper.get_predicted_remaining_budget(log, campaign)
    threshold = _get_threshold(campaign_state)
    is_below = predicted < threshold
    log.add_context({
        'predicted': predicted,
        'is_below_threshold': is_below,
        'threshold': threshold,
    })
    return is_below


def _get_threshold(campaign_state):
    if campaign_state.state == constants.CampaignStopState.STOPPED:
        # NOTE: avoid restarting when a stopped campaign only slightly above threshold is checked
        return THRESHOLD * decimal.Decimal('1.5')
    return THRESHOLD
