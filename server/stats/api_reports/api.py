from django.utils.text import slugify

import redshiftapi.api_reports
import dash.dashapi.api_reports

import dash.export

from stats import api_breakdowns
from stats import constants
from stats import helpers
from stats import permission_filter

from utils import sort_helper
from utils import columns

from format_helper import format_values


def query(user, breakdown, constraints, goals, order, level, columns, include_items_with_no_spend=False):
    stats_rows = redshiftapi.api_reports.query(
        breakdown, constraints, goals, order,
        use_publishers_view=api_breakdowns.should_use_publishers_view(breakdown))

    if include_items_with_no_spend:
        dash_rows = dash.dashapi.api_reports.query(user, breakdown, constraints, level)
        rows = helpers.merge_rows(breakdown, dash_rows, stats_rows)
    else:
        rows = stats_rows
        dash.dashapi.api_reports.annotate(rows, user, breakdown, constraints, level)

    rows = sort_helper.sort_results(rows, [order])

    format_values(rows, columns)

    permission_filter.filter_columns_by_permission(user, rows, goals)

    return rows


def totals(user, breakdown, constraints, goals, level, columns):
    rows = redshiftapi.api_reports.query_totals(
        breakdown, constraints, goals,
        use_publishers_view=api_breakdowns.should_use_publishers_view(breakdown))

    assert len(rows) == 1

    dash.dashapi.api_reports.annotate_totals(rows[0], user, breakdown, constraints, level)

    format_values(rows, columns)

    permission_filter.filter_columns_by_permission(user, rows, goals)

    return rows[0]


def get_filename(breakdown, constraints):

    if constraints['allowed_accounts'].count() == 1:
        account_name = slugify(constraints['allowed_accounts'][0].name)
    else:
        account_name = 'ZemantaOne'

    campaign_name = None
    if constraints['allowed_campaigns'] is not None and constraints['allowed_campaigns'].count() == 1:
        campaign_name = slugify(constraints['allowed_campaigns'][0].name)

    ad_group_name = None
    if constraints['allowed_ad_groups'] is not None and constraints['allowed_ad_groups'].count() == 1:
        ad_group_name = slugify(constraints['allowed_ad_groups'][0].name)

    breakdown = ['by_' + getattr(columns.ColumnNames, constants.get_dimension_name_key(x)).lower() for x in breakdown]
    return '_'.join(filter(None, [
        account_name,
        campaign_name,
        ad_group_name,
        '_'.join(breakdown),
        'report',
        constraints['date__gte'].isoformat(),
        constraints['date__lte'].isoformat(),
    ]))
