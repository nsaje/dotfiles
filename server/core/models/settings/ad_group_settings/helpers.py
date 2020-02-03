from django.db import transaction

from core.features import bid_modifiers
from dash import constants
from utils import zlogging

logger = zlogging.getLogger(__name__)


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
    for ad_group_source, source_bid in list(ad_group_sources_bids.items()):
        ad_group_source_settings = ad_group_source.get_current_settings()

        if bidding_type == constants.BiddingType.CPC:
            if ad_group_source_settings.cpc_cc == source_bid:
                bid_modifiers.create_source_bid_modifier(
                    ad_group, ad_group_source.source, ad_group_settings.cpc, source_bid
                )
                continue
        else:
            if ad_group_source_settings.cpm == source_bid:
                bid_modifiers.create_source_bid_modifier(
                    ad_group, ad_group_source.source, ad_group_settings.cpm, source_bid
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


def check_b1_sources_group_bid_changed(ad_group_settings, changes):
    if ad_group_settings.ad_group.bidding_type == constants.BiddingType.CPM:
        return "b1_sources_group_cpm" in changes
    else:
        return "b1_sources_group_cpc_cc" in changes


def calculate_ad_group_sources_bids(ad_group_settings, b1_sources_group_bid_changed):
    adjusted_bids = {}
    campaign_goal = _get_campaign_goal(ad_group_settings)
    for ad_group_source in ad_group_settings.ad_group.adgroupsource_set.all().select_related(
        "source__source_type", "settings"
    ):
        bid_value = (
            ad_group_settings.cpm
            if ad_group_settings.ad_group.bidding_type == constants.BiddingType.CPM
            else ad_group_settings.cpc
        )
        source_bid = bid_modifiers.source.calculate_source_bid_value(
            bid_value, ad_group_settings.ad_group, str(ad_group_source.source.id)
        )
        source_bid = _replace_with_b1_sources_group_bid_if_needed(
            source_bid, ad_group_source, ad_group_settings, campaign_goal, b1_sources_group_bid_changed
        )
        source_bid = _threshold_autopilot_bid_if_needed(ad_group_settings, source_bid)
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


def _threshold_autopilot_bid_if_needed(ad_group_settings, proposed_bid):
    if (
        ad_group_settings.autopilot_state != constants.AdGroupSettingsAutopilotState.INACTIVE
        and ad_group_settings.max_autopilot_bid
        and proposed_bid > ad_group_settings.max_autopilot_bid
    ):
        return ad_group_settings.max_autopilot_bid

    return proposed_bid
