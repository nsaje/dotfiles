from utils import sort_helper
from utils import queryset_helper

import dash.constants
import stats.constants
import stats.helpers

from dash import publisher_group_helpers

from redshiftapi import api_breakdowns
from redshiftapi import postprocess


__all__ = ['query', 'query_totals']


def query(breakdown, constraints, goals, order='-media_cost', use_publishers_view=False):
    constraints = extract_constraints(constraints)

    rows = api_breakdowns._query_all(
        breakdown, constraints, None, goals, use_publishers_view,
        breakdown_for_name=breakdown, extra_name='reports_all')
    rows = sort_helper.sort_results(rows, [order])
    postprocess.set_default_values(breakdown, rows)
    return rows


def query_totals(breakdown, constraints, goals, use_publishers_view=False):
    constraints = extract_constraints(constraints)

    rows = api_breakdowns._query_all([], constraints, None, goals, use_publishers_view,
                                     breakdown_for_name=breakdown, extra_name='report_totals')
    postprocess.set_default_values([], rows)
    return rows


def extract_constraints(constraints):
    new_constraints = {
        'date__gte': constraints['date__gte'],
        'date__lte': constraints['date__lte'],
    }

    mapping = {
        'allowed_accounts': 'account_id',
        'allowed_campaigns': 'campaign_id',
        'allowed_ad_groups': 'ad_group_id',
        'allowed_content_ads': 'content_ad_id',
        'filtered_sources': 'source_id',
    }

    for key, column in mapping.items():
        if constraints.get(key) is not None:
            new_constraints[column] = queryset_helper.get_pk_list(constraints[key])

    if 'publisher_blacklist_filter' in constraints and \
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
