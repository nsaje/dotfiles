# isort:skip_file
from functools import partial

from utils import threads

import dash.models
import dash.campaign_goals

from stats import helpers
from stats import constants
from stats import augmenter
from stats import permission_filter

# expose these helpers as API
from stats.helpers import get_goals, Goals

import redshiftapi.api_breakdowns
import dash.dashapi.api_breakdowns


# define the API
__all__ = ["query", "totals", "validate_breakdown_allowed", "get_goals", "Goals"]


def validate_breakdown_allowed(level, user, breakdown):
    permission_filter.validate_breakdown_by_structure(breakdown)
    permission_filter.validate_breakdown_by_permissions(level, user, breakdown)


def should_use_publishers_view(breakdown):
    return "publisher_id" in breakdown and "content_ad_id" not in breakdown


def query(level, user, breakdown, constraints, goals, parents, order, offset, limit):
    """
    Get a breakdown report. Data is sourced from dash models and redshift.

    All field names and values in breakdown, constraints, parents and order should
    use valid field names. Field names should match those of used in dash and redshiftapi models.
    """

    helpers.check_constraints_are_supported(constraints)
    helpers.log_user_query_request(user, breakdown, constraints, order, offset, limit)

    target_dimension = constants.get_target_dimension(breakdown)

    order = helpers.extract_order_field(order, target_dimension, goals.primary_goals)

    parents = helpers.decode_parents(breakdown, parents)
    stats_constraints = helpers.extract_stats_constraints(constraints, breakdown)

    should_query_dashapi = helpers.should_query_dashapi(target_dimension)
    if should_query_dashapi:
        queries = dash.dashapi.api_breakdowns.query_async_start(level, user, breakdown, constraints, parents)

    if helpers.should_query_dashapi_first(order, target_dimension):
        dash_rows = dash.dashapi.api_breakdowns.query_async_get_results(queries, breakdown, order, offset, limit)
        stats_rows = redshiftapi.api_breakdowns.query_stats_for_rows(
            dash_rows, breakdown, stats_constraints, goals, use_publishers_view=should_use_publishers_view(breakdown)
        )
        rows = helpers.merge_rows(breakdown, dash_rows, stats_rows)
    else:
        if should_query_dashapi and offset > 0:
            query_structure_fn = partial(
                redshiftapi.api_breakdowns.query_structure_with_stats,
                breakdown,
                stats_constraints,
                use_publishers_view=should_use_publishers_view(breakdown),
            )
            structure_thread = threads.AsyncFunction(query_structure_fn)
            structure_thread.start()

        stats_rows = redshiftapi.api_breakdowns.query_with_background_cache(
            breakdown,
            stats_constraints,
            parents,
            goals,
            helpers.extract_rs_order_field(order, target_dimension),
            offset,
            limit,
            use_publishers_view=should_use_publishers_view(breakdown),
        )
        if should_query_dashapi:
            if offset == 0:
                str_w_stats = stats_rows
            else:
                structure_thread.join()
                str_w_stats = structure_thread.get_result()

            dash_rows = dash.dashapi.api_breakdowns.query_async_get_results_for_rows(
                queries, stats_rows, breakdown, parents, order, offset, limit, str_w_stats
            )
            rows = helpers.merge_rows(breakdown, dash_rows, stats_rows)
        else:
            rows = stats_rows

    augmenter.augment(breakdown, rows)
    augmenter.cleanup(rows, target_dimension, constraints)

    permission_filter.filter_columns_by_permission(user, rows, goals, constraints, level)

    return rows


def totals(user, level, breakdown, constraints, goals):
    helpers.check_constraints_are_supported(constraints)

    stats_rows = redshiftapi.api_breakdowns.query_totals(
        breakdown,
        helpers.extract_stats_constraints(constraints, breakdown),
        goals,
        use_publishers_view=should_use_publishers_view(breakdown),
    )

    dash_total_row = dash.dashapi.api_breakdowns.get_totals(level, user, breakdown, constraints)

    for k, v in list(dash_total_row.items()):
        stats_rows[0][k] = v

    permission_filter.filter_columns_by_permission(user, stats_rows, goals, constraints, level)

    return stats_rows[0]
