from celery.exceptions import SoftTimeLimitExceeded
from django.db import transaction

import core.models
from server import celery
from utils import metrics_compat
from utils import zlogging

from .. import CampaignStopState
from .. import constants
from ..campaign_event_processed_at import CampaignEventProcessedAt
from . import mark_almost_depleted_campaigns
from . import update_campaigns_end_date
from . import update_campaigns_start_date
from . import update_campaigns_state

logger = zlogging.getLogger(__name__)


@celery.app.task(acks_late=True, name="campaignstop_update_handler", soft_time_limit=60 * 60, ignore_result=True)
def handle_updates(campaign_id, campaign_type, time):
    try:
        _handle_updates(campaign_id, campaign_type, time)
    except SoftTimeLimitExceeded:
        logger.warning("Time limit exceeded", campaign_id=campaign_id, type=campaign_type)


def _handle_updates(campaign_id, campaign_type, time):
    campaign = _get_campaign(campaign_id)
    with transaction.atomic():
        campaign_processed_record, created = CampaignEventProcessedAt.objects.get_or_create(
            campaign=campaign, type=campaign_type
        )
        if created or campaign_processed_record.modified_dt.timestamp() < time:
            with metrics_compat.block_timer("campaignstop.update_handler.process_campaign", type=campaign_type):
                _process_campaign(campaign, campaign_type)
        campaign_processed_record.update_modified_dt()


def _get_campaign(campaign_id):
    campaign = core.models.Campaign.objects.filter(id=campaign_id).first()
    return campaign


def _process_campaign(campaign, type):
    if type == constants.CampaignUpdateType.BUDGET:
        _handle_budget_updates(campaign)
    elif type == constants.CampaignUpdateType.DAILY_CAP:
        _handle_daily_cap_updates(campaign)
    elif type == constants.CampaignUpdateType.INITIALIZATION:
        _handle_initialize(campaign)
    elif type == constants.CampaignUpdateType.CAMPAIGNSTOP_STATE:
        _handle_campaignstopstate_change(campaign)


def _handle_initialize(campaign):
    logger.info("Handle initialize campaign", campaign=campaign.id)
    _full_check(campaign)


def _handle_budget_updates(campaign):
    logger.info("Handle campaign budget update", campaign=campaign.id)
    _full_check(campaign)
    _unset_pending_updates(campaign)


def _unset_pending_updates(campaign):
    campaignstop_state, _ = CampaignStopState.objects.get_or_create(campaign=campaign.id)
    campaignstop_state.update_pending_budget_updates(False)


def _handle_campaignstopstate_change(campaign):
    logger.info("Handle campaign stop state change", campaign=campaign.id)
    update_campaigns_start_date([campaign])


def _full_check(campaign):
    update_campaigns_end_date([campaign])
    update_campaigns_start_date([campaign])

    update_campaigns_state([campaign])
    mark_almost_depleted_campaigns([campaign])


def _handle_daily_cap_updates(campaign):
    logger.info("Handle campaign daily cap update", campaign=campaign)
    mark_almost_depleted_campaigns([campaign])
