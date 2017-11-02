import backtosql
import collections
import copy
import datetime
import dateutil
from dash import publisher_helpers

from utils import dates_helper
from utils import sort_helper

import stats.helpers
from stats import constants


def create_parents(rows, breakdown):
    parent_breakdown = constants.get_parent_breakdown(breakdown)
    target_dimension = constants.get_target_dimension(breakdown)

    groups = sort_helper.group_rows_by_breakdown_key(parent_breakdown, rows)

    parents = []
    for group_key, child_rows in groups.iteritems():
        parent = stats.helpers.get_breakdown_id(child_rows[0], parent_breakdown)
        parent[target_dimension] = [row[target_dimension] for row in child_rows]
        parents.append(parent)

    return parents


def inflate_parent_constraints(parents):
    """
    Modify parent constraints so that proper columns are constrained.
    """

    new_parents = []

    for parent in parents:
        if 'publisher_id' in parent:
            # publisher_id is an aggregate so not the most suitable for a constraint
            new_parent = copy.copy(parent)

            publisher_id = new_parent.pop('publisher_id')
            publisher, source_id = publisher_helpers.dissect_publisher_id(publisher_id)

            new_parent['publisher'] = publisher

            if source_id:
                new_parent['source_id'] = source_id

            new_parents.append(new_parent)
        else:
            new_parents.append(parent)

    return new_parents


def optimize_parent_constraints(parents):
    other_parents = []
    one_field_values = collections.defaultdict(list)
    source_publishers = collections.defaultdict(list)

    for parent in parents:
        # this will make an 'IN' statement instead of many 'OR' statements
        if len(parent) == 1:
            field_name = parent.keys()[0]
            val = parent[field_name]
            if backtosql.is_collection(val):
                one_field_values[field_name].extend(val)
            else:
                one_field_values[field_name].append(val)

        # special publisher optimization
        elif len(parent) == 2 and 'source_id' in parent and 'publisher' in parent:
            source_id = parent['source_id']
            publisher = parent['publisher']
            if backtosql.is_collection(publisher):
                source_publishers[source_id].extend(publisher)
            else:
                source_publishers[source_id].append(publisher)
        else:
            other_parents.append(parent)

    parents = other_parents
    if one_field_values:
        parents.extend([{k: v[0] if len(v) == 1 else v} for k, v in one_field_values.items()])

    if source_publishers:
        parents.extend([
            {'source_id': k, 'publisher': v} for k, v in source_publishers.items()
        ])

    return parents


def merge_rows(breakdown, rows, stats_rows):
    group_stats_rows = sort_helper.group_rows_by_breakdown_key(breakdown, stats_rows)

    for row in rows:
        breakdown_key = sort_helper.get_breakdown_key(row, breakdown)
        stats_row = group_stats_rows.get(breakdown_key, None)

        if stats_row:
            row.update(stats_row[0])

    return rows


def select_relevant_stats_rows(breakdown, rows, stats_rows):
    # returns stats_rows that match rows

    group_stats_rows = sort_helper.group_rows_by_breakdown_key(breakdown, stats_rows, max_1=True)
    group_rows = sort_helper.group_rows_by_breakdown_key(breakdown, rows, max_1=True)
    return [stat_row for breakdown_key, stat_row in group_stats_rows.iteritems() if breakdown_key in group_rows]


def get_all_dimensions(breakdown, constraints, parents):
    # TODO this should take dimensions from a model to be reliable, also base view_selecter on model fields
    constraints_dimensions = set(backtosql.dissect_constraint_key(x)[0] for x in constraints.keys())
    parents_dimensions = set(backtosql.dissect_constraint_key(x)[0] for parent in parents for x in parent.keys()) if parents else set([])
    breakdown_dimensions = set(breakdown)

    non_date_dimensions = set(constants.StructureDimension._ALL) | set(constants.DeliveryDimension._ALL)

    return (constraints_dimensions | parents_dimensions | breakdown_dimensions) & non_date_dimensions


def get_yesterday_constraints(constraints):
    constraints = copy.copy(constraints)
    constraints.pop('date__gte', None)
    constraints.pop('date__lte', None)
    constraints['date'] = dates_helper.local_yesterday()

    return constraints


def get_time_dimension_constraints(time_dimension, constraints, offset, limit):
    """
    Sets time constraints so that they fit offset and limit. Instead of
    using SQL offset and limit just adjust the date range so the scan space
    is smaller.
    """

    constraints = copy.copy(constraints)

    start_date = constraints['date__gte']

    if time_dimension == constants.TimeDimension.DAY:
        start_date = start_date + datetime.timedelta(days=offset)
        end_date = _safe_date_add(start_date, datetime.timedelta(days=limit))

    elif time_dimension == constants.TimeDimension.WEEK:
        start_date = start_date + datetime.timedelta(days=7 * offset)
        end_date = _safe_date_add(start_date, datetime.timedelta(days=7 * limit))

    else:
        start_date = start_date.replace(day=1)
        start_date = start_date + dateutil.relativedelta.relativedelta(months=offset)
        end_date = _safe_date_add(start_date, dateutil.relativedelta.relativedelta(months=limit))

    constraints['date__gte'] = max(start_date, constraints['date__gte'])
    if min(end_date, constraints['date__lte']) == constraints['date__lte']:
        # end of date range - fetch until the end
        constraints['date__lte'] = constraints['date__lte']
    else:
        # else later ranges are possible
        del constraints['date__lte']
        constraints['date__lte'] = end_date - datetime.timedelta(days=1)
    return constraints


def _safe_date_add(date, timedelta):
    try:
        return date + timedelta
    except OverflowError:
        return datetime.date.max


def get_query_name(breakdown, extra_name=''):
    if extra_name:
        extra_name = '__' + extra_name

    return '__'.join(breakdown) + extra_name


def is_pixel_metric(metric):
    return (
        metric.startswith('pixel_') or
        metric.startswith('avg_cost_per_pixel_')
    )


def is_conversion_goal_metric(metric):
    return (
        metric.startswith('conversion_goal_') or
        metric.startswith('avg_cost_per_conversion_goal_')
    )
