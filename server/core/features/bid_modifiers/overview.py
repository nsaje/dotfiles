import functools
import operator

from django.db.models import Max
from django.db.models import Min

from . import models


def get_min_max_factors(ad_group_id, included_types=None, excluded_types=None):
    query_set = models.BidModifier.objects.filter(ad_group__id=ad_group_id)

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
