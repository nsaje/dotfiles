import json

from django.conf import settings

import core.entity
from . import mark_almost_depleted_campaigns
from . import update_campaigns_state
from . import refresh_realtime_data
from . import update_campaigns_end_date
from .. import constants

from utils import sqs_helper


def handle_updates():
    messages = _get_messages_from_queue()

    budget_campaigns = _extract_campaigns(_filter_messages(constants.CampaignUpdateType.BUDGET, messages))
    if budget_campaigns:
        _handle_budget_updates(budget_campaigns)

    daily_cap_campaigns = _extract_campaigns(_filter_messages(constants.CampaignUpdateType.DAILY_CAP, messages))
    if daily_cap_campaigns:
        _handle_daily_cap_updates(daily_cap_campaigns)


def _get_messages_from_queue():
    messages = sqs_helper.get_all_messages(settings.CAMPAIGN_STOP_UPDATE_HANDLER_QUEUE)
    return [json.loads(message.get_body()) for message in messages]


def _handle_budget_updates(campaigns):
    update_campaigns_end_date(campaigns)

    refresh_realtime_data(campaigns)
    mark_almost_depleted_campaigns(campaigns)
    update_campaigns_state(campaigns)


def _handle_daily_cap_updates(campaigns):
    refresh_realtime_data(campaigns)
    mark_almost_depleted_campaigns(campaigns)


def _filter_messages(type_, messages):
    return [message for message in messages if message['type'] == type_]


def _extract_campaigns(messages):
    campaign_ids = [message['campaign_id'] for message in messages]
    return core.entity.Campaign.objects.filter(id__in=campaign_ids)
