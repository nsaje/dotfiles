import logging

from django.conf import settings

from utils import sqs_helper

from .. import constants

logger = logging.getLogger(__name__)


AD_GROUP_SETTINGS_FIELDS = [
    "state",
    "b1_sources_group_state",
    "b1_sources_group_daily_budget",
    "start_date",
    "end_date",
]
AD_GROUP_SOURCE_SETTINGS_FIELDS = ["daily_budget_cc", "state"]


def notify_initialize(campaign):
    _notify(campaign, constants.CampaignUpdateType.INITIALIZATION)


def notify_ad_group_settings_change(ad_group_settings, changes):
    if _has_changed(changes, AD_GROUP_SETTINGS_FIELDS):
        campaign = ad_group_settings.ad_group.campaign
        _notify(campaign, constants.CampaignUpdateType.DAILY_CAP)


def notify_ad_group_source_settings_change(ad_group_source_settings, changes):
    if _has_changed(changes, AD_GROUP_SOURCE_SETTINGS_FIELDS):
        campaign = ad_group_source_settings.ad_group_source.ad_group.campaign
        _notify(campaign, constants.CampaignUpdateType.DAILY_CAP)


def notify_campaignstopstate_change(campaign):
    _notify(campaign, constants.CampaignUpdateType.CAMPAIGNSTOP_STATE)


def _has_changed(changes, relevant_fields):
    return any(field in relevant_fields for field in changes)


def notify_budget_line_item_change(campaign):
    _notify(campaign, constants.CampaignUpdateType.BUDGET)


def _notify(campaign, type_):
    if not campaign.real_time_campaign_stop:
        return
    logger.info("Notify campaign update: campaign_id=%s, type=%s", campaign.id, type_)
    sqs_helper.write_message_json(
        settings.CAMPAIGN_STOP_UPDATE_HANDLER_QUEUE, {"campaign_id": campaign.id, "type": type_}
    )
