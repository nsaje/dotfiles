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


def apply_parent_to_rows(parent, rows):
    for row in rows:
        row.update(parent)
    return rows


def needs_to_query_additional_rows(target_ids, limit):
    return len(target_ids) < limit


def get_adjusted_limits_for_additional_rows(target_ids, all_taken_ids, offset, limit):
    limit = limit - len(target_ids)
    offset = max(offset - len(all_taken_ids), 0)
    return offset, limit


def get_used_ids(target_dimension, rows_with_stats, parent_dimension, parent_id):
    if parent_dimension is None:
        return [x[target_dimension] for x in rows_with_stats]
    return [x[target_dimension] for x in rows_with_stats if x[parent_dimension] == parent_id]


def get_allowed_constraints_field(target_dimension):
    if target_dimension == 'account_id':
        return 'allowed_accounts'
    elif target_dimension == 'campaign_id':
        return 'allowed_campaigns'
    elif target_dimension == 'ad_group_id':
        return 'allowed_ad_groups'
    elif target_dimension == 'content_ad_id':
        return 'allowed_content_ads'
    elif target_dimension == 'source_id':
        return 'filtered_sources'


def group_rows_by_parents(rows, parent_dimension, target_dimension, flat=False, parents=None):
    if flat:
        return [(None, rows, [row[target_dimension] for row in rows])]

    by_parent = collections.defaultdict(list)
    for row in rows:
        by_parent[row[parent_dimension]].append(row)

    # initialize also those parents that do not have associated rows
    # these way we also add keys with empty lists
    for parent in (parents or []):
        parent_rows = by_parent[parent[parent_dimension]]
        if not parent_rows:
            by_parent[parent[parent_dimension]] = []

    return [(k, v, [row[target_dimension] for row in v]) for k, v in by_parent.items()]


def select_active_ad_group_sources(level, constraints, parent_dimension, parent_id,
                                   source_ids_subselection=None):
    if level is Level.ALL_ACCOUNTS:
        modelcls = models.Account
        objs = constraints['allowed_accounts']
        if parent_dimension == 'account_id':
            objs = objs.filter(pk=parent_id)

    elif level is Level.ACCOUNTS:
        if parent_dimension is None:
            modelcls = models.Account
            objs = [constraints['account']]
        elif parent_dimension == 'campaign_id':
            modelcls = models.Campaign
            objs = constraints['allowed_campaigns'].filter(pk=parent_id)

    elif level is Level.CAMPAIGNS:
        if parent_dimension is None:
            modelcls = models.Campaign
            objs = [constraints['campaign']]
        elif parent_dimension == 'ad_group_id':
            modelcls = models.AdGroup
            objs = constraints['allowed_ad_groups'].filter(pk=parent_id)

    elif level is Level.AD_GROUPS:
        modelcls = models.AdGroup
        objs = [constraints['ad_group']]

    sources = constraints['filtered_sources']
    if source_ids_subselection:
        sources = sources.filter(pk__in=source_ids_subselection)

    ad_group_sources = get_active_ad_group_sources(modelcls, objs)
    return sources, ad_group_sources
