import collections
import copy
import datetime
from dateutil import rrule, relativedelta

import newrelic.agent

from utils import sort_helper

from dash import constants as dash_constants

from stats import constants


"""
Apply any modifications to reports that should be returned by redshiftapi as data source
but are easier to do in python than in sql.
"""


@newrelic.agent.function_trace()
def postprocess_breakdown_query(rows, empty_row, breakdown, constraints, parents, order, offset, limit):
    target_dimension = constants.get_target_dimension(breakdown)

    if target_dimension in constants.TimeDimension._ALL:
        postprocess_time_dimension(
            target_dimension, rows, empty_row, breakdown, constraints, parents)
        return sort_helper.sort_results(rows, [order])

    if target_dimension == 'device_type':
        postprocess_device_type_dimension(
            target_dimension, rows, empty_row, breakdown, parents, offset, limit)
        return sort_helper.sort_results(rows, [order])
    return rows


def postprocess_time_dimension(target_dimension, rows, empty_row, breakdown, constraints, parent):
    """
    When querying time dimensions add rows that are missing from a query
    so that result is a nice constant time series.
    """

    all_dates = _get_representative_dates(target_dimension, constraints)
    fill_in_missing_rows(
        target_dimension, rows, empty_row, breakdown, parent, all_dates)


def postprocess_device_type_dimension(target_dimension, rows, empty_row, breakdown, parent,
                                      offset, limit):
    all_values = sorted(dash_constants.DeviceType._VALUES.keys())

    fill_in_missing_rows(
        target_dimension, rows, empty_row, breakdown, parent,
        all_values[offset:offset + limit]
    )


def fill_in_missing_rows(target_dimension, rows, empty_row, breakdown, parent, all_values):
    parent_breakdown = constants.get_parent_breakdown(breakdown)

    rows_per_parent_breakdown = collections.defaultdict(list)
    for row in rows:
        parent_br_key = _get_breakdown_key_tuple(parent_breakdown, row)
        rows_per_parent_breakdown[parent_br_key].append(row)

    for bc in parent:
        parent_br_key = _get_breakdown_key_tuple(parent_breakdown, bc)

        # collect used constants for rows returned
        used = set(row[target_dimension] for row in rows_per_parent_breakdown[parent_br_key])

        for x in all_values:
            if x not in used:
                new_row = copy.copy(empty_row)
                new_row.update(bc)  # update with parent
                new_row[target_dimension] = x

                rows_per_parent_breakdown[parent_br_key].append(new_row)
                rows.append(new_row)

        # cut rows that are not a part of the final collection
        for x in used:
            if x not in all_values:
                excess_row = [row for row in rows_per_parent_breakdown[parent_br_key] if row[target_dimension] == x][0]

                rows.remove(excess_row)


def _get_breakdown_key_tuple(breakdown, row_or_dict):
    return tuple(row_or_dict[dimension] for dimension in breakdown)


def _get_representative_dates(time_dimension, constraints):
    """
    Returns dates that represent time dimension values within constraints.
    This logics should be synced with how we query time dimensions from
    database.
    """

    start_date = constraints['date__gte']
    end_date = constraints.get('date__lte')
    if end_date is None:
        end_date = constraints['date__lt'] - datetime.timedelta(days=1)

    if time_dimension == constants.TimeDimension.DAY:
        dates = rrule.rrule(rrule.DAILY, start_date, until=end_date)
    elif time_dimension == constants.TimeDimension.WEEK:
        # all weeks in the span starting monday
        dates = rrule.rrule(
            rrule.WEEKLY,
            start_date + relativedelta.relativedelta(weekday=relativedelta.MO(-1)),
            until=end_date, byweekday=rrule.MO)
    else:
        # all months starting 1st
        dates = rrule.rrule(
            rrule.MONTHLY,
            start_date + relativedelta.relativedelta(day=1),
            until=end_date
        )

    return list(x.date() for x in dates)
