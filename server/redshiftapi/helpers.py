import backtosql
import collections
import copy

import stats.helpers
from stats import constants


POSTCLICK_FIELDS = [
    'visits', 'click_discrepancy', 'pageviews', 'new_visits', 'percent_new_users', 'bounce_rate',
    'pv_per_visit', 'avg_tos', 'returning_users', 'unique_users', 'new_users', 'bounced_visits',
    'total_seconds', 'avg_cost_per_minute', 'non_bounced_visits', 'avg_cost_per_non_bounced_visit',
    'total_pageviews', 'avg_cost_per_pageview', 'avg_cost_for_new_visitor', 'avg_cost_per_visit',
]


def remove_postclick_values(breakdown, rows):
    # HACK: Temporary hack that removes postclick data when we breakdown by delivery
    if constants.get_delivery_dimension(breakdown) is not None:
        for row in rows:
            for key in POSTCLICK_FIELDS:
                row[key] = None


def create_parents(rows, breakdown):
    parent_breakdown = constants.get_parent_breakdown(breakdown)
    target_dimension = constants.get_target_dimension(breakdown)

    groups = stats.helpers.group_rows_by_breakdown(parent_breakdown, rows)

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
            publisher, source_id = stats.helpers.dissect_publisher_id(publisher_id)

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
    group_stats_rows = stats.helpers.group_rows_by_breakdown(breakdown, stats_rows)

    for row in rows:
        breakdown_id = stats.helpers.get_breakdown_id_tuple(row, breakdown)
        stats_row = group_stats_rows.get(breakdown_id, None)

        if stats_row:
            row.update(stats_row[0])

    return rows


def get_all_dimensions(breakdown, constraints, parents, use_publishers_view):
    constraints_dimensions = set(backtosql.dissect_constraint_key(x)[0] for x in constraints.keys())
    parents_dimensions = set(backtosql.dissect_constraint_key(x)[0] for parent in parents for x in parent.keys()) if parents else set([])
    breakdown_dimensions = set(breakdown)

    non_date_dimensions = set(constants.StructureDimension._ALL) | set(constants.DeliveryDimension._ALL)

    if use_publishers_view:
        breakdown_dimensions.add('publisher_id')

    return (constraints_dimensions | parents_dimensions | breakdown_dimensions) & non_date_dimensions
