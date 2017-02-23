from redshiftapi import api_breakdowns
from redshiftapi import postprocess

import dash.constants

from utils import sort_helper


__all__ = ['query']


def query(breakdown, metrics, constraints, goals, order, use_publishers_view=False):
    constraints = extract_constraints(constraints, use_publishers_view)

    rows = api_breakdowns._query_all(
        breakdown, constraints, None, goals, use_publishers_view,
        breakdown_for_name=breakdown, extra_name='dailystats_all',
        metrics=metrics)
    postprocess.set_default_values(breakdown, rows)
    rows = sort_helper.sort_results(rows, [order])

    return rows


def extract_constraints(constraints, use_publishers_view):
    # TODO currently only handles ad group/publishers view

    new_constraints = {
        'date__gte': constraints['date__gte'],
        'date__lte': constraints['date__lte'],
        'source_id': list(constraints['filtered_sources'].values_list('pk', flat=True).order_by('pk')),
        'account_id': (constraints['account'].id if 'account' in constraints else
                       list(constraints['allowed_accounts'].values_list('pk', flat=True).order_by('pk'))),
    }

    if 'ad_group' in constraints:
        new_constraints['ad_group_id'] = constraints['ad_group'].id

    if 'campaign' in constraints:
        new_constraints['campaign_id'] = constraints['campaign'].id

    if 'account' in constraints:
        new_constraints['account_id'] = constraints['account'].id

    if use_publishers_view and \
       constraints['publisher_blacklist_filter'] != dash.constants.PublisherBlacklistFilter.SHOW_ALL:
        if constraints['publisher_blacklist_filter'] == dash.constants.PublisherBlacklistFilter.SHOW_ACTIVE:
            new_constraints['publisher_id__neq'] = list(
                constraints['publisher_blacklist'].annotate_publisher_id().values_list('publisher_id', flat=True))
        elif constraints['publisher_blacklist_filter'] == dash.constants.PublisherBlacklistFilter.SHOW_BLACKLISTED:
            new_constraints['publisher_id'] = list(
                constraints['publisher_blacklist'].annotate_publisher_id().values_list('publisher_id', flat=True))
        elif constraints['publisher_blacklist_filter'] == dash.constants.PublisherBlacklistFilter.SHOW_WHITELISTED:
            new_constraints['publisher_id'] = list(
                constraints['publisher_whitelist'].annotate_publisher_id().values_list('publisher_id', flat=True))

    return new_constraints
