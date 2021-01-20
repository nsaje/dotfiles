import dataclasses
import decimal
import functools
import operator
from typing import Dict
from typing import List
from typing import Optional
from typing import Sequence
from typing import Tuple
from typing import Union

from django.db.models import CharField
from django.db.models import Count
from django.db.models import Max
from django.db.models import Min
from django.db.models import QuerySet
from django.db.models.functions import Cast

import core.models
import dash.constants

from . import constants
from . import helpers
from . import models


@dataclasses.dataclass
class BidModifierTypeSummary:
    type: int
    count: int
    min: float
    max: float


def get_min_max_local_bids(
    ad_group: core.models.AdGroup,
    included_types: Union[None, Sequence[int]] = None,
    excluded_types: Union[None, Sequence[int]] = None,
) -> Tuple[decimal.Decimal, Optional[decimal.Decimal]]:
    bid = (
        ad_group.settings.local_cpc
        if ad_group.bidding_type == dash.constants.BiddingType.CPC
        else ad_group.settings.local_cpm
    )

    if bid is None:
        return decimal.Decimal(0.0001), None

    min_factor, max_factor = get_min_max_factors(
        ad_group.id, included_types=included_types, excluded_types=excluded_types
    )

    return decimal.Decimal(min_factor) * bid, decimal.Decimal(max_factor) * bid


def get_min_max_factors(
    ad_group_id: int,
    included_types: Union[None, Sequence[int]] = None,
    excluded_types: Union[None, Sequence[int]] = None,
) -> Tuple[float, float]:
    query_set = models.BidModifier.objects.filter(ad_group__id=ad_group_id)

    if included_types is not None:
        query_set = query_set.filter(type__in=included_types)

    if excluded_types is not None:
        query_set = query_set.exclude(type__in=excluded_types)

    min_max_list = [
        _calculate_min_max(ad_group_id, e["type"], e["count"], e["min"], e["max"])
        for e in _get_overview_queryset(ad_group_id, included_types=included_types, excluded_types=excluded_types)
    ]

    min_factor = functools.reduce(operator.mul, [e["min"] for e in min_max_list], 1.0)
    max_factor = functools.reduce(operator.mul, [e["max"] for e in min_max_list], 1.0)

    return min_factor, max_factor


def get_type_summaries(
    ad_group_id: int,
    included_types: Union[None, Sequence[int]] = None,
    excluded_types: Union[None, Sequence[int]] = None,
) -> List[BidModifierTypeSummary]:
    query_set = models.BidModifier.objects.filter(ad_group__id=ad_group_id)

    if included_types is not None:
        query_set = query_set.filter(type__in=included_types)

    if excluded_types is not None:
        query_set = query_set.exclude(type__in=excluded_types)

    modifiers = [
        BidModifierTypeSummary(**kwargs)
        for kwargs in _get_overview_queryset(ad_group_id, included_types=included_types, excluded_types=excluded_types)
    ]

    for modifier in modifiers:
        result = _calculate_min_max(ad_group_id, modifier.type, modifier.count, modifier.min, modifier.max)
        modifier.min = result["min"]
        modifier.max = result["max"]

    return modifiers


def _get_overview_queryset(
    ad_group_id: int,
    included_types: Union[None, Sequence[int]] = None,
    excluded_types: Union[None, Sequence[int]] = None,
) -> QuerySet:
    query_set = models.BidModifier.objects.filter(ad_group__id=ad_group_id)

    if included_types is not None:
        query_set = query_set.filter(type__in=included_types)

    if excluded_types is not None:
        query_set = query_set.exclude(type__in=excluded_types)

    return (
        query_set.values("type")
        .annotate(count=Count("type"))
        .distinct()
        .annotate(min=Min("modifier"), max=Max("modifier"))
        .values("type", "count", "min", "max")
        .order_by("type")
    )


def _calculate_min_max(
    ad_group_id: int, modifier_type: int, count: int, min_value: float, max_value: float
) -> Dict[str, float]:
    if modifier_type in (
        constants.BidModifierType.PUBLISHER,
        constants.BidModifierType.COUNTRY,
        constants.BidModifierType.STATE,
        constants.BidModifierType.DMA,
        constants.BidModifierType.PLACEMENT,
    ):
        # for these dimensions we can not easily deduce exact min and max, thus we are expanding the range with 1 if applicable
        min_value, max_value = _min_max_with_ones(min_value, max_value)

    elif modifier_type in (
        constants.BidModifierType.DEVICE,
        constants.BidModifierType.OPERATING_SYSTEM,
        constants.BidModifierType.ENVIRONMENT,
        constants.BidModifierType.BROWSER,
        constants.BidModifierType.CONNECTION_TYPE,
    ):
        if count != _get_dimension_constant_count(modifier_type) - 1:  # account for UNKNOWN
            min_value, max_value = _min_max_with_ones(min_value, max_value)

    elif modifier_type == constants.BidModifierType.DAY_HOUR:
        if count != _get_dimension_constant_count(modifier_type):
            min_value, max_value = _min_max_with_ones(min_value, max_value)

    elif modifier_type == constants.BidModifierType.SOURCE:
        # TODO subquery could be used to reduce number of DB queries, but there are problems with getting active sources count
        active_sources_ids = list(
            core.models.AdGroupSource.objects.filter(ad_group_id=ad_group_id)
            .filter_active()
            .annotate(target=Cast("source__id", CharField()))
            .values_list("target", flat=True)
        )
        result = models.BidModifier.objects.filter(
            ad_group_id=ad_group_id, type=constants.BidModifierType.SOURCE, target__in=active_sources_ids
        ).aggregate(min=Min("modifier"), max=Max("modifier"), bid_modifier_count=Count("ad_group"))

        min_value = result["min"] if result["min"] is not None else 1.0
        max_value = result["max"] if result["max"] is not None else 1.0

        if len(active_sources_ids) != result["bid_modifier_count"]:
            min_value, max_value = _min_max_with_ones(min_value, max_value)

    elif modifier_type == constants.BidModifierType.AD:
        # TODO subquer could be used to reduce number of DB queriesy, but there are problems with getting active sources count
        active_content_ad_ids = list(
            core.models.ContentAd.objects.filter(ad_group_id=ad_group_id)
            .filter_active()
            .annotate(target=Cast("id", CharField()))
            .values_list("target", flat=True)
        )

        result = models.BidModifier.objects.filter(
            ad_group_id=ad_group_id, type=constants.BidModifierType.AD, target__in=active_content_ad_ids
        ).aggregate(min=Min("modifier"), max=Max("modifier"), bid_modifier_count=Count("ad_group"))

        min_value = result["min"] if result["min"] is not None else 1.0
        max_value = result["max"] if result["max"] is not None else 1.0

        if len(active_content_ad_ids) != result["bid_modifier_count"]:
            min_value, max_value = _min_max_with_ones(min_value, max_value)

    else:
        raise ValueError("Invalid bid modifier type {}".format(modifier_type))

    return {"min": min_value, "max": max_value}


def _min_max_with_ones(min_value, max_value):
    return min(min_value, 1), max(max_value, 1)


def _get_dimension_constant_count(bid_modifier_type):
    constant, _ = helpers.modifier_type_to_constant_dimension(bid_modifier_type)
    return len(constant.get_all())
