import collections
import copy
import datetime
from dateutil import rrule, relativedelta

from stats import constants


"""
Apply any modifications to reports that should be returned by redshiftapi as data source
but are easier to do in python than in sql.
"""


def postprocess_time_dimension(time_dimension, rows, empty_row, breakdown, constraints, breakdown_constraints):
    """
    When querying time dimensions add rows that are missing from a query
    so that result is a nice constant time series.
    """

    parent_breakdown = constants.get_parent_breakdown(breakdown)

    # map rows by parent breakdown
    rows_per_parent_breakdown = collections.defaultdict(list)
    for row in rows:
        parent_br_key = _get_breakdown_key_tuple(parent_breakdown, row)
        rows_per_parent_breakdown[parent_br_key].append(row)

    all_dates = _get_representative_dates(time_dimension, constraints)

    # breakdown constraints represent parent selection
    for bc in breakdown_constraints:
        parent_br_key = _get_breakdown_key_tuple(parent_breakdown, bc)

        # collect used dates from rows returned
        used_dates = set(row[time_dimension] for row in rows_per_parent_breakdown[parent_br_key])

        for missing_date in set(all_dates) - set(used_dates):
            new_row = copy.copy(empty_row)
            new_row.update(bc)  # update with parent
            new_row[time_dimension] = missing_date

            rows.append(new_row)

    # TODO sort rows


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
