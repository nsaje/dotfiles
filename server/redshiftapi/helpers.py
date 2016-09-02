from stats.helpers import group_rows_by_breakdown, get_breakdown_id, get_breakdown_id_tuple
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

    groups = group_rows_by_breakdown(parent_breakdown, rows)

    parents = []
    for group_key, child_rows in groups.iteritems():
        parent = get_breakdown_id(child_rows[0], parent_breakdown)
        parent[target_dimension] = [row[target_dimension] for row in child_rows]
        parents.append(parent)

    return parents


def merge_rows(breakdown, rows, stats_rows):
    group_stats_rows = group_rows_by_breakdown(breakdown, stats_rows)

    for row in rows:
        breakdown_id = get_breakdown_id_tuple(row, breakdown)
        stats_row = group_stats_rows.get(breakdown_id, None)

        if stats_row:
            row.update(stats_row[0])

    return rows
