from decimal import Decimal

import dash.constants
import dash.models
from utils import decimal_helpers

from . import constants
from . import service


def calculate_source_bid_value(ad_group_bid_value, ad_group, target):
    bid_modifier = (
        dash.models.BidModifier.objects.only("modifier")
        .filter(type=constants.BidModifierType.SOURCE, ad_group=ad_group, target=target)
        .first()
    )

    if bid_modifier is not None:
        modifier = Decimal(bid_modifier.modifier)
    else:
        modifier = Decimal("1.0000")

    return decimal_helpers.multiply_as_decimals(ad_group_bid_value, modifier)


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


def create_source_bid_modifier(ad_group, source, ad_group_bid_value, ad_group_source_bid_value):
    modifier = Decimal(ad_group_source_bid_value) / Decimal(ad_group_bid_value)

    service.set(
        ad_group,
        constants.BidModifierType.SOURCE,
        str(source.id),
        None,
        float(modifier),
        user=None,
        write_history=False,
        propagate_to_k1=False,
    )
