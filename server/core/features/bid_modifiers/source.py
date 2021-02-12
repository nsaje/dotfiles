from decimal import Decimal

import dash.constants
import dash.models
from utils import decimal_helpers

from . import constants
from . import service


def calculate_source_bid_values_map(ad_group_bid_value, ad_group, source_ids):
    bid_modifiers = dash.models.BidModifier.objects.filter(
        type=constants.BidModifierType.SOURCE, ad_group=ad_group, target__in=[str(i) for i in source_ids]
    ).values("modifier", "target")

    bid_modifiers_map = {int(bm["target"]): Decimal(bm["modifier"]) for bm in bid_modifiers}

    bid_values_map = {}
    for source_id in source_ids:
        modifier = bid_modifiers_map.get(source_id, Decimal("1.0000"))
        bid_values_map[source_id] = decimal_helpers.multiply_as_decimals(ad_group_bid_value, modifier)

    return bid_values_map


def handle_ad_group_source_settings_change(
    ad_group_source_settings, changes, user=None, system_user=None, write_history=True, k1_sync=False
):
    if not set(changes.keys()) & {"cpc_cc", "cpm"}:
        # change not related to bid value
        return

    if ad_group_source_settings.ad_group_source.ad_group.bidding_type == dash.constants.BiddingType.CPC:
        if "cpc_cc" not in changes:
            return

        modifier = Decimal(changes["cpc_cc"]) / Decimal(ad_group_source_settings.ad_group_source.ad_group.settings.cpc)
    else:
        if "cpm" not in changes:
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
        skip_source_settings_update=True,
    )


def create_source_bid_modifier_data(source, ad_group_bid_value, ad_group_source_bid_value):
    modifier = Decimal(ad_group_source_bid_value) / Decimal(ad_group_bid_value)

    return service.BidModifierData(constants.BidModifierType.SOURCE, str(source.id), None, float(modifier))
