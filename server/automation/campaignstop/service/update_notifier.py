import logging

from utils import sqs_helper
from django.conf import settings

from .. import constants


logger = logging.getLogger(__name__)


def notify_initialize(campaign):
    _notify(campaign.id, constants.CampaignUpdateType.INITIALIZATION)


def notify_ad_group_settings_change(ad_group_settings, changes):
    if 'state' in changes or\
       'b1_sources_group_state' in changes or\
       'b1_sources_group_daily_budget' in changes:
        campaign = ad_group_settings.ad_group.campaign
        _notify(campaign, constants.CampaignUpdateType.DAILY_CAP)


def notify_ad_group_source_settings_change(ad_group_source_settings, changes):
    if 'daily_budget_cc' in changes or 'state' in changes:
        campaign = ad_group_source_settings.ad_group_source.ad_group.campaign
        _notify(campaign, constants.CampaignUpdateType.DAILY_CAP)


def notify_budget_line_item_change(campaign):
    _notify(campaign, constants.CampaignUpdateType.BUDGET)


def _notify(campaign, type_):
    if not campaign.real_time_campaign_stop:
        return
    logger.info('Notify campaign update: campaign_id=%s, type=%s', campaign.id, type_)
    sqs_helper.write_message_json(
        settings.CAMPAIGN_STOP_UPDATE_HANDLER_QUEUE,
        {'campaign_id': campaign.id, 'type': type_}
    )
