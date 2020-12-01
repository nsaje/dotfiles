import time

from utils import zlogging

from .. import constants
from .update_handler import handle_updates

logger = zlogging.getLogger(__name__)


AD_GROUP_SETTINGS_FIELDS = [
    "state",
    "local_b1_sources_group_state",
    "local_b1_sources_group_daily_budget",
    "start_date",
    "end_date",
    "local_daily_budget",
]
AD_GROUP_SOURCE_SETTINGS_FIELDS = ["local_daily_budget_cc", "state"]


def notify_initialize(campaign):
    notify(campaign, constants.CampaignUpdateType.INITIALIZATION)


def notify_ad_group_settings_change(ad_group_settings, changes):
    if _has_changed(changes, AD_GROUP_SETTINGS_FIELDS):
        campaign = ad_group_settings.ad_group.campaign
        notify(campaign, constants.CampaignUpdateType.DAILY_CAP)


def notify_ad_group_source_settings_change(ad_group_source_settings, changes):
    if _has_changed(changes, AD_GROUP_SOURCE_SETTINGS_FIELDS):
        campaign = ad_group_source_settings.ad_group_source.ad_group.campaign
        notify(campaign, constants.CampaignUpdateType.DAILY_CAP)


def _has_changed(changes, relevant_fields):
    return any(field in relevant_fields for field in changes)


def notify_campaignstopstate_change(campaign):
    notify(campaign, constants.CampaignUpdateType.CAMPAIGNSTOP_STATE)


def notify_budget_line_item_change(campaign):
    notify(campaign, constants.CampaignUpdateType.BUDGET)


def notify(campaign, type_):
    if not campaign.real_time_campaign_stop:
        return
    logger.debug("Notify campaign update", campaign_id=campaign.id, type=type_)
    handle_updates.delay(campaign.id, type_, _time())


def _time():
    return time.time()
