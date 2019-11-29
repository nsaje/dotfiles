import dataclasses
import functools
import operator
from typing import List
from typing import Sequence
from typing import Tuple
from typing import Union

from django.db.models import Count
from django.db.models import Max
from django.db.models import Min

from . import constants
from . import models


@dataclasses.dataclass
class BidModifierTypeSummary:
    type: int
    count: int
    min: float
    max: float


def get_min_max_factors(
    ad_group_id: int,
    included_types: Union[None, Sequence[int]] = None,
    excluded_types: Union[None, Sequence[int]] = None,
) -> Tuple[float, float]:
    query_set = models.BidModifier.objects.filter(ad_group__id=ad_group_id)

    # TEMP(tkusterle) temporarily disable source bid modifiers
    excluded_types = set(excluded_types) if excluded_types else set()  # type: ignore
    excluded_types.add(constants.BidModifierType.SOURCE)  # type: ignore

    if included_types is not None:
        query_set = query_set.filter(type__in=included_types)

    if excluded_types is not None:
        query_set = query_set.exclude(type__in=excluded_types)

    min_max_list = list(
        query_set.values("type")
        .distinct()
        .annotate(min_modifier=Min("modifier"), max_modifier=Max("modifier"))
        .values("type", "min_modifier", "max_modifier")
    )

    min_factor = functools.reduce(operator.mul, [min(e["min_modifier"], 1.) for e in min_max_list], 1.)
    max_factor = functools.reduce(operator.mul, [max(e["max_modifier"], 1.) for e in min_max_list], 1.)

    return min_factor, max_factor


def get_type_summaries(
    ad_group_id: int,
    included_types: Union[None, Sequence[int]] = None,
    excluded_types: Union[None, Sequence[int]] = None,
    include_ones: bool = True,
) -> List[BidModifierTypeSummary]:
    query_set = models.BidModifier.objects.filter(ad_group__id=ad_group_id)

    # TEMP(tkusterle) temporarily disable source bid modifiers
    excluded_types = set(excluded_types) if excluded_types else set()  # type: ignore
    excluded_types.add(constants.BidModifierType.SOURCE)  # type: ignore

    if included_types is not None:
        query_set = query_set.filter(type__in=included_types)

    if excluded_types is not None:
        query_set = query_set.exclude(type__in=excluded_types)

    modifiers = [
        BidModifierTypeSummary(**kwargs)
        for kwargs in query_set.values("type")
        .annotate(count=Count("type"))
        .distinct()
        .annotate(min=Min("modifier"), max=Max("modifier"))
        .values("type", "count", "min", "max")
        .order_by("type")
    ]

    if include_ones:
        for entry in modifiers:
            if entry.max < 1:
                entry.max = 1.0
            elif entry.min > 1:
                entry.min = 1.0

    return modifiers
