import collections

from dash.constants import Level
from dash.views.helpers import get_active_ad_group_sources
from dash import models


def apply_offset_limit(qs, offset, limit):
    if offset and limit:
        return qs[offset:offset + limit]

    if offset:
        return qs[offset:]

    if limit:
        return qs[:limit]

    return qs


def get_adjusted_limits_for_additional_rows(target_ids, all_taken_ids, offset, limit):
    limit = limit - len(target_ids)
    offset = max(offset - len(all_taken_ids), 0)
    return offset, limit
