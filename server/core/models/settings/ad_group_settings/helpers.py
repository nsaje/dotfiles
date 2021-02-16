from django.db import transaction

from core.features import bid_modifiers
from dash import constants
from utils import zlogging

logger = zlogging.getLogger(__name__)

BROWSER_DEVICE_MAPPING = {
    constants.BrowserFamily.OTHER: [
        constants.AdTargetDevice.DESKTOP,
        constants.AdTargetDevice.TABLET,
        constants.AdTargetDevice.MOBILE,
    ],
    constants.BrowserFamily.CHROME: [
        constants.AdTargetDevice.DESKTOP,
        constants.AdTargetDevice.TABLET,
        constants.AdTargetDevice.MOBILE,
    ],
    constants.BrowserFamily.FIREFOX: [
        constants.AdTargetDevice.DESKTOP,
        constants.AdTargetDevice.TABLET,
        constants.AdTargetDevice.MOBILE,
    ],
    constants.BrowserFamily.SAFARI: [
        constants.AdTargetDevice.DESKTOP,
        constants.AdTargetDevice.TABLET,
        constants.AdTargetDevice.MOBILE,
    ],
    constants.BrowserFamily.IE: [constants.AdTargetDevice.DESKTOP],
    constants.BrowserFamily.SAMSUNG: [constants.AdTargetDevice.TABLET, constants.AdTargetDevice.MOBILE],
    constants.BrowserFamily.OPERA: [
        constants.AdTargetDevice.DESKTOP,
        constants.AdTargetDevice.TABLET,
        constants.AdTargetDevice.MOBILE,
    ],
    constants.BrowserFamily.UC_BROWSER: [
        constants.AdTargetDevice.DESKTOP,
        constants.AdTargetDevice.TABLET,
        constants.AdTargetDevice.MOBILE,
    ],
    constants.BrowserFamily.IN_APP: [constants.AdTargetDevice.TABLET, constants.AdTargetDevice.MOBILE],
    constants.BrowserFamily.EDGE: [
        constants.AdTargetDevice.DESKTOP,
        constants.AdTargetDevice.TABLET,
        constants.AdTargetDevice.MOBILE,
    ],
}


@transaction.atomic
def set_ad_group_sources_bids(
    bidding_type,
    ad_group_sources_bids,
    ad_group,
    ad_group_settings,
    skip_validation=False,
    skip_notification=False,
    write_source_history=True,
):
    bid_modifier_list = []

    for ad_group_source, source_bid in list(ad_group_sources_bids.items()):
        ad_group_source_settings = ad_group_source.get_current_settings()

        if bidding_type == constants.BiddingType.CPC:
            if ad_group_source_settings.cpc_cc == source_bid:
                bid_modifier_list.append(
                    bid_modifiers.create_source_bid_modifier_data(
                        ad_group_source.source, ad_group_settings.cpc, source_bid
                    )
                )
                continue
        else:
            if ad_group_source_settings.cpm == source_bid:
                bid_modifier_list.append(
                    bid_modifiers.create_source_bid_modifier_data(
                        ad_group_source.source, ad_group_settings.cpm, source_bid
                    )
                )
                continue

        update_kwargs = {
            "k1_sync": False,
            "skip_validation": skip_validation,
            "skip_notification": skip_notification,
            "write_history": write_source_history,
        }
        if bidding_type == constants.BiddingType.CPC:
            update_kwargs["cpc_cc"] = source_bid
        else:
            update_kwargs["cpm"] = source_bid

        ad_group_source.settings.update(**update_kwargs)

    if bid_modifier_list:
        bid_modifiers.set_bulk(
            ad_group, bid_modifier_list, user=None, write_history=False, propagate_to_k1=False, skip_validation=True
        )


def check_max_autopilot_bid_changed(ad_group_settings, changes):
    autopilot_state = changes.get("autopilot_state", ad_group_settings.autopilot_state)
    return autopilot_state != constants.AdGroupSettingsAutopilotState.INACTIVE and "local_max_autopilot_bid" in changes


def calculate_ad_group_sources_bids(ad_group_settings, max_autopilot_bid_changed, b1_sources_group_bid_changed):
    adjusted_bids = {}
    campaign_goal = _get_campaign_goal(ad_group_settings)
    ad_group_source_list = list(
        ad_group_settings.ad_group.adgroupsource_set.select_related("source", "source__source_type", "settings")
    )
    source_bid_values_map = bid_modifiers.source.calculate_source_bid_values_map(
        ad_group_settings.bid, ad_group_settings.ad_group, [ags.source.id for ags in ad_group_source_list]
    )

    for ad_group_source in ad_group_source_list:
        source_bid = source_bid_values_map.get(ad_group_source.source.id)
        source_bid = _replace_with_b1_sources_group_bid_if_needed(
            source_bid, ad_group_source, ad_group_settings, campaign_goal, b1_sources_group_bid_changed
        )
        source_bid = _adjust_to_autopilot_bid_if_needed(
            ad_group_settings, source_bid, max_autopilot_bid_changed=max_autopilot_bid_changed
        )
        adjusted_bids[ad_group_source] = source_bid
    return adjusted_bids


def _get_campaign_goal(ad_group_settings):
    try:
        campaign_goal = ad_group_settings.ad_group.campaign.campaigngoal_set.get(primary=True)
    except Exception:
        campaign_goal = None
    return campaign_goal


def _replace_with_b1_sources_group_bid_if_needed(
    source_bid, ad_group_source, ad_group_settings, campaign_goal, b1_sources_group_bid_changed
):
    if (
        ad_group_settings.b1_sources_group_enabled
        and ad_group_source.source.source_type.type == constants.SourceType.B1
        and (
            ad_group_settings.autopilot_state != constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET
            or (campaign_goal and campaign_goal.type != constants.CampaignGoalKPI.CPA)
        )
    ):
        if not b1_sources_group_bid_changed:
            return source_bid

        source_bid = (
            ad_group_settings.b1_sources_group_cpm
            if ad_group_settings.ad_group.bidding_type == constants.BiddingType.CPM
            else ad_group_settings.b1_sources_group_cpc_cc
        )

    return source_bid


def _adjust_to_autopilot_bid_if_needed(ad_group_settings, proposed_bid, max_autopilot_bid_changed=False):
    if ad_group_settings.max_autopilot_bid and (
        max_autopilot_bid_changed
        or (
            ad_group_settings.autopilot_state != constants.AdGroupSettingsAutopilotState.INACTIVE
            and ad_group_settings.max_autopilot_bid
            and proposed_bid > ad_group_settings.max_autopilot_bid
        )
    ):
        proposed_bid = ad_group_settings.max_autopilot_bid
    return proposed_bid


def adjust_to_autopilot_bid_if_needed(ad_group_settings, max_autopilot_bid_changed):
    if ad_group_settings.max_autopilot_bid and max_autopilot_bid_changed:
        bid_modifiers.delete_types(ad_group_settings.ad_group, [bid_modifiers.BidModifierType.SOURCE])


def get_browser_targeting_errors(browsers, target_devices):
    browser_errors = []
    for browser in browsers:
        valid = any(device in BROWSER_DEVICE_MAPPING[browser["family"]] for device in target_devices)
        error = {"family": ["Invalid browser and device type combination configuration"]} if not valid else {}
        browser_errors.append(error)
    return browser_errors
