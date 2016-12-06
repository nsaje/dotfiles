import datetime
from django.utils.text import slugify

import redshiftapi.api_reports
import dash.dashapi.api_reports

import dash.export

from stats import api_breakdowns
from stats import constants
from stats import permission_filter

from utils import sort_helper
from utils import columns


def query(user, breakdown, constraints, goals, order):
    rows = redshiftapi.api_reports.query(
        breakdown, constraints, goals, order,
        use_publishers_view=api_breakdowns.should_use_publishers_view(breakdown))

    dash.dashapi.api_reports.annotate(rows, user, breakdown, constraints, goals)
    annotate(rows)

    rows = sort_helper.sort_results(rows, [order])

    permission_filter.filter_columns_by_permission(user, rows, goals)

    return rows


def totals(user, breakdown, constraints, goals):
    rows = redshiftapi.api_reports.query_totals(
        breakdown, constraints, goals,
        use_publishers_view=api_breakdowns.should_use_publishers_view(breakdown))

    assert len(rows) == 1

    annotate(rows)

    permission_filter.filter_columns_by_permission(user, rows, goals)

    return rows[0]


def get_filename(breakdown, constraints):

    if constraints['allowed_accounts'].count() == 1:
        account_name = slugify(constraints['allowed_accounts'][0].name)
    else:
        account_name = 'ZemantaOne'

    campaign_name = None
    if constraints['allowed_campaigns'].count() == 1:
        campaign_name = slugify(constraints['allowed_campaigns'][0].name)

    ad_group_name = None
    if constraints['allowed_ad_groups'].count() == 1:
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


def annotate(rows):
    for row in rows:
        for column, value in row.items():
            value = dash.export._format_empty_value(value, column)
            value = dash.export._format_percentages(value, column)
            value = dash.export._format_decimals(value, column)
            value = dash.export._format_hash(value, column)
            value = format_date(value, column)
            value = format_week(value, column)
            value = format_month(value, column)
            row[column] = value


def format_date(value, column):
    if column == constants.TimeDimension.DAY:
        if not value:
            return ''
        value = value.strftime('%Y-%m-%d')
    return value


def format_week(value, column):
    if column == constants.TimeDimension.WEEK:
        value = "Week {} - {}".format(
            value.isoformat(), (value + datetime.timedelta(days=6)).isoformat())
    return value


def format_month(value, column):
    if column == constants.TimeDimension.MONTH:
        value = "Month {}/{}".format(value.month, value.year)
    return value
