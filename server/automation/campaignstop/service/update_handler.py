import time
from collections import defaultdict

import structlog
from django.conf import settings

import core.models
from utils import sqs_helper

from .. import CampaignStopState
from .. import constants
from . import mark_almost_depleted_campaigns
from . import update_campaigns_end_date
from . import update_campaigns_start_date
from . import update_campaigns_state

logger = structlog.get_logger(__name__)


MAX_MESSAGES_TO_FETCH = 5000
CAMPAIGNS_PER_BATCH = 100
MAX_JOB_DURATION_SECONDS = 4 * 60 + 30


def handle_updates():
    start_time = _time()
    with sqs_helper.process_json_messages(
        settings.CAMPAIGN_STOP_UPDATE_HANDLER_QUEUE, limit=MAX_MESSAGES_TO_FETCH
    ) as messages:
        updates_by_campaign = _get_updates_by_campaign(messages)

        campaigns = list(updates_by_campaign.keys())
        while campaigns:
            campaigns_batch, campaigns = campaigns[:CAMPAIGNS_PER_BATCH], campaigns[CAMPAIGNS_PER_BATCH:]
            _process_batch({campaign: updates_by_campaign[campaign] for campaign in campaigns_batch})
            if _time() - start_time > MAX_JOB_DURATION_SECONDS:
                break
        if campaigns:
            logger.info(
                "Out of time for processing - sending updates for %s campaigns back to the queue. Campaigns: %s",
                len(campaigns),
                ",".join(map(str, [c.id for c in campaigns])),
            )
            _notify_remaining_campaigns(campaigns, updates_by_campaign)


def _time():
    return time.time()


def _get_updates_by_campaign(messages):
    campaigns_map = {campaign.id: campaign for campaign in _extract_campaigns(messages)}
    updates_by_campaign = defaultdict(set)
    for message in messages:
        campaign_id = message["campaign_id"]
        if campaign_id not in campaigns_map:
            logger.warning("Received an update for non-existing campaign", campaign_id=campaign_id)
            continue
        campaign = campaigns_map[campaign_id]
        updates_by_campaign[campaign].add(message["type"])
    return updates_by_campaign


def _notify_remaining_campaigns(campaigns, updates_by_campaign):
    from . import notify

    for campaign in campaigns:
        for update in updates_by_campaign[campaign]:
            notify(campaign, update)


def _process_batch(batch):
    campaigns_by_update = _get_campaigns_by_type(batch)
    budget_campaigns = campaigns_by_update[constants.CampaignUpdateType.BUDGET]
    if budget_campaigns:
        _handle_budget_updates(budget_campaigns)

    daily_cap_campaigns = campaigns_by_update[constants.CampaignUpdateType.DAILY_CAP]
    if daily_cap_campaigns:
        _handle_daily_cap_updates(daily_cap_campaigns)

    initialize_campaigns = campaigns_by_update[constants.CampaignUpdateType.INITIALIZATION]
    if initialize_campaigns:
        _handle_initialize(initialize_campaigns)

    campaignstopstate_campaigns = campaigns_by_update[constants.CampaignUpdateType.CAMPAIGNSTOP_STATE]
    if campaignstopstate_campaigns:
        _handle_campaignstopstate_change(campaignstopstate_campaigns)


def _get_campaigns_by_type(updates_by_campaign):
    campaigns_by_update = {type_: [] for type_ in constants.CampaignUpdateType.get_all()}
    for campaign, updates in updates_by_campaign.items():
        for update in updates:
            campaigns_by_update[update].append(campaign)
    return campaigns_by_update


def _extract_campaigns(messages):
    campaign_ids = [message["campaign_id"] for message in messages]
    return core.models.Campaign.objects.filter(id__in=campaign_ids)


def _handle_initialize(campaigns):
    logger.info("Handle initialize campaign", campaigns=[campaign.id for campaign in campaigns])
    _full_check(campaigns)


def _handle_budget_updates(campaigns):
    logger.info("Handle campaign budget update", campaigns=[campaign.id for campaign in campaigns])
    _full_check(campaigns)
    _unset_pending_updates(campaigns)


def _unset_pending_updates(campaigns):
    for campaign in campaigns:
        campaignstop_state, _ = CampaignStopState.objects.get_or_create(campaign=campaign)
        campaignstop_state.update_pending_budget_updates(False)


def _handle_campaignstopstate_change(campaigns):
    logger.info("Handle campaign stop state change", campaigns=[campaign.id for campaign in campaigns])
    update_campaigns_start_date(campaigns)


def _full_check(campaigns):
    update_campaigns_end_date(campaigns)
    update_campaigns_start_date(campaigns)

    update_campaigns_state(campaigns)
    mark_almost_depleted_campaigns(campaigns)


def _handle_daily_cap_updates(campaigns):
    logger.info("Handle campaign daily cap update", campaigns=[campaign.id for campaign in campaigns])
    mark_almost_depleted_campaigns(campaigns)
