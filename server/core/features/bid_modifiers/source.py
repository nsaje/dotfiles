from decimal import Decimal

from django.db.models import F

import dash.constants
import dash.models

from . import constants
from . import service


def handle_ad_group_settings_change(
    ad_group_settings, changes, user=None, system_user=None, write_history=False, k1_sync=False
):
    if not set(changes.keys()) & {"cpc", "cpm"}:
        # change not related to bid value
        return

    # TEMP(tkusterle) when we stop using max bid values the implementation
    # will change to recalculate ad group source bid values

    if ad_group_settings.ad_group.bidding_type == dash.constants.BiddingType.CPC:
        if "cpc" not in changes:
            return

        ad_group_bid_value = changes["cpc"]
        annotation_kwargs = {"bid_value": F("settings__cpc_cc")}
    else:
        if "cpm" not in changes:
            return

        ad_group_bid_value = changes["cpm"]
        annotation_kwargs = {"bid_value": F("settings__cpm")}

    source_bid_modifiers = _calculate_bid_modifiers_for_all_sources(
        ad_group_settings.ad_group, ad_group_bid_value, annotation_kwargs
    )

    service.set_from_cleaned_entries(
        ad_group_settings.ad_group,
        source_bid_modifiers,
        user=user,
        write_history=write_history,
        propagate_to_k1=k1_sync,
    )


def handle_ad_group_source_settings_change(
    ad_group_source_settings, changes, user=None, system_user=None, write_history=False, k1_sync=False
):
    if not set(changes.keys()) & {"cpc_cc", "cpm"}:
        # change not related to bid value
        return

    if ad_group_source_settings.ad_group_source.ad_group.bidding_type == dash.constants.BiddingType.CPC:
        if "cpc_cc" not in changes or ad_group_source_settings.ad_group_source.ad_group.settings.cpc is None:
            # ad_group.settings.cpc is not expected to be None, this is just a temporary safeguard
            return

        modifier = Decimal(changes["cpc_cc"]) / Decimal(ad_group_source_settings.ad_group_source.ad_group.settings.cpc)
    else:
        if "cpm" not in changes or ad_group_source_settings.ad_group_source.ad_group.settings.cpm is None:
            # ad_group.settings.cpm is not expected to be None, this is just a temporary safeguard
            return

        modifier = Decimal(changes["cpm"]) / Decimal(ad_group_source_settings.ad_group_source.ad_group.settings.cpm)

    service.set(
        ad_group_source_settings.ad_group_source.ad_group,
        constants.BidModifierType.SOURCE,
        str(ad_group_source_settings.ad_group_source.source.id),
        None,
        float(modifier),
        user=user,
        write_history=write_history,
        propagate_to_k1=k1_sync,
    )


def handle_bidding_type_change(ad_group, user=None):
    # TEMP(tkusterle) will be changed to keep bid modifier values and update source bid values

    if ad_group.bidding_type == dash.constants.BiddingType.CPC:
        ad_group_bid_value = ad_group.settings.cpc
        annotation_kwargs = {"bid_value": F("settings__cpc_cc")}
    else:
        ad_group_bid_value = ad_group.settings.cpm
        annotation_kwargs = {"bid_value": F("settings__cpm")}

    source_bid_modifiers = _calculate_bid_modifiers_for_all_sources(ad_group, ad_group_bid_value, annotation_kwargs)

    service.set_from_cleaned_entries(
        ad_group, source_bid_modifiers, user=user, write_history=False, propagate_to_k1=False
    )


def _calculate_bid_modifiers_for_all_sources(ad_group, ad_group_bid_value, annotation_kwargs):
    return [
        {
            "type": constants.BidModifierType.SOURCE,
            "target": str(e["source__id"]),
            "source": None,
            "modifier": float(Decimal(e["bid_value"]) / Decimal(ad_group_bid_value)),
        }
        for e in dash.models.AdGroupSource.objects.filter(ad_group=ad_group)
        .annotate(**annotation_kwargs)
        .values("source__id", "bid_value")
    ]
