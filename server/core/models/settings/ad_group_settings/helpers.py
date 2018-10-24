import logging

from django.db import transaction

from dash import constants
from dash import cpc_constraints

logger = logging.getLogger(__name__)


def get_adjusted_ad_group_sources_bids(ad_group, ad_group_settings):
    adjusted_bids = {}
    for ad_group_source in ad_group.adgroupsource_set.all().select_related(
        "source__source_type",
        "settings",
        "ad_group__settings",
        "ad_group__campaign__settings",
        "ad_group__campaign__account__agency",
    ):
        if (
            ad_group_source.source.source_type.type != constants.SourceType.B1
            and ad_group_source.get_current_settings().state == constants.AdGroupSourceSettingsState.INACTIVE
        ):
            continue

        ags_settings = ad_group_source.get_current_settings()
        proposed_bid = ags_settings.cpm if ad_group.bidding_type == constants.BiddingType.CPM else ags_settings.cpc_cc
        adjusted_bid = _get_adjusted_ad_group_source_bid(
            proposed_bid, ad_group_source, ad_group_settings, ad_group.campaign.settings
        )
        adjusted_bids[ad_group_source] = adjusted_bid
    return adjusted_bids


def validate_ad_group_sources_cpc_constraints(bcm_modifiers, ad_group_sources_cpcs, ad_group):
    rules_per_source = cpc_constraints.get_rules_per_source(ad_group, bcm_modifiers)
    for ad_group_source, proposed_cpc in list(ad_group_sources_cpcs.items()):
        if proposed_cpc:
            cpc_constraints.validate_cpc(proposed_cpc, rules=rules_per_source[ad_group_source.source])


@transaction.atomic
def set_ad_group_sources_cpcs(ad_group_sources_cpcs, ad_group, ad_group_settings, skip_validation=False):
    rules_per_source = cpc_constraints.get_rules_per_source(ad_group)
    for ad_group_source, proposed_cpc in list(ad_group_sources_cpcs.items()):
        adjusted_cpc = _get_adjusted_ad_group_source_bid(
            proposed_cpc, ad_group_source, ad_group_settings, ad_group.campaign.settings
        )
        if adjusted_cpc:
            adjusted_cpc = cpc_constraints.adjust_cpc(adjusted_cpc, rules=rules_per_source[ad_group_source.source])

        ad_group_source_settings = ad_group_source.get_current_settings()
        if ad_group_source_settings.cpc_cc == adjusted_cpc:
            continue
        ad_group_source.settings.update(cpc_cc=adjusted_cpc, k1_sync=False, skip_validation=skip_validation)


@transaction.atomic
def set_ad_group_sources_cpms(ad_group_sources_cpms, ad_group, ad_group_settings, skip_validation=False):
    for ad_group_source, proposed_cpm in list(ad_group_sources_cpms.items()):
        adjusted_cpm = _get_adjusted_ad_group_source_bid(
            proposed_cpm, ad_group_source, ad_group_settings, ad_group.campaign.settings
        )
        ad_group_source_settings = ad_group_source.get_current_settings()
        if ad_group_source_settings.cpm == adjusted_cpm:
            continue
        ad_group_source.settings.update(cpm=adjusted_cpm, k1_sync=False, skip_validation=skip_validation)


def _get_adjusted_ad_group_source_bid(proposed_bid, ad_group_source, ad_group_settings, campaign_settings):
    if (
        ad_group_settings.b1_sources_group_enabled
        and ad_group_source.source.source_type.type == constants.SourceType.B1
        and ad_group_settings.autopilot_state != constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET
        and not campaign_settings.autopilot
    ):
        proposed_bid = (
            ad_group_settings.b1_sources_group_cpm
            if ad_group_settings.ad_group.bidding_type == constants.BiddingType.CPM
            else ad_group_settings.b1_sources_group_cpc_cc
        )
    return adjust_max_bid(proposed_bid, ad_group_settings)


def adjust_max_bid(proposed_bid, ad_group_settings):
    max_bid = (
        ad_group_settings.max_cpm
        if ad_group_settings.ad_group.bidding_type == constants.BiddingType.CPM
        else ad_group_settings.cpc_cc
    )

    if not (proposed_bid and max_bid):
        return proposed_bid

    if proposed_bid > max_bid:
        return max_bid

    return proposed_bid