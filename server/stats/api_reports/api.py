import datetime

import redshiftapi.api_reports
import dash.dashapi.api_reports

import dash.export

from stats import api_breakdowns
from stats import constants

from utils import sort_helper


def query(user, breakdown, constraints, goals, order):
    rows = redshiftapi.api_reports.query(
        breakdown, constraints, goals, order,
        use_publishers_view=api_breakdowns.should_use_publishers_view(breakdown))

    dash.dashapi.api_reports.annotate(rows, user, breakdown, constraints, goals, order)
    annotate(rows, breakdown)

    rows = sort_helper.sort_results(rows, [order])

    return rows


def annotate(rows, breakdown):
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
