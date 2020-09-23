# isort:skip_file
from functools import partial

import newrelic.agent

from utils import threads
from utils import sort_helper

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
__all__ = [
    "query",
    "totals",
    "counts",
    "validate_breakdown_allowed",
    "get_goals",
    "Goals",
    "should_use_publishers_view",
]


@newrelic.agent.function_trace()
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

    should_query_dashapi = helpers.should_query_dashapi(breakdown, target_dimension)
    if should_query_dashapi:
        queries = dash.dashapi.api_breakdowns.query_async_start(level, user, breakdown, constraints, parents)

    if helpers.should_query_dashapi_first(order, target_dimension):
        if target_dimension == constants.StructureDimension.SOURCE:
            """
            IMPORTANT
            ------------------------------------------
            We must first query RDS for source_id breakdown in order to avoid a bug
            with sorting, pagination and removing deprecated sources with no stats.

            SAMPLE STATE:
            ------------------------------------------
            - RDS entries: s1, s2, s3 (deprecated), s4, s5, s6, s7
            - RS entries: s1, s2, s3, s6, s7
            - count: 7 (we have 7 sources with stats or not deprecated)

            BUG DESCRIPTION:
            ------------------------------------------
            - offset: 6
            - limit: 2
            - expected result: s7 (because count is 7)
            - actual result: None (INFINITE load more)

            BUG REASON:
            ------------------------------------------
            - RDS returns 7 rows, RS return 0 rows (because of offset, limit)
            - merge (s1...s7) but s3 is deprecated and with not stats
            - s3 is removed from the result set
            - in memory we apply offset/limit cut
            - [s1, s2, s4, s5, s6, s7][6:7] = []
            """
            dash_rows = dash.dashapi.api_breakdowns.query_async_get_results(queries, breakdown)
            stats_rows = redshiftapi.api_breakdowns.query_stats_for_rows(
                dash_rows,
                breakdown,
                stats_constraints,
                goals,
                use_publishers_view=should_use_publishers_view(breakdown),
            )
            rows = helpers.merge_rows(breakdown, dash_rows, stats_rows)
            augmenter.remove_deprecated_sources_with_no_stats(rows, constraints)
            rows = sort_helper.sort_rows_by_order_and_archived(
                rows, [order] + dash.dashapi.api_breakdowns.get_default_order(target_dimension, order)
            )
            rows = sort_helper.apply_offset_limit(rows, offset, limit)
        else:
            dash_rows = dash.dashapi.api_breakdowns.query_async_get_results(queries, breakdown, order, offset, limit)
            stats_rows = redshiftapi.api_breakdowns.query_stats_for_rows(
                dash_rows,
                breakdown,
                stats_constraints,
                goals,
                use_publishers_view=should_use_publishers_view(breakdown),
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
                _join_structure_thread(structure_thread)
                str_w_stats = structure_thread.get_result()

            dash_rows = dash.dashapi.api_breakdowns.query_async_get_results_for_rows(
                queries, stats_rows, breakdown, parents, order, offset, limit, str_w_stats
            )
            rows = helpers.merge_rows(breakdown, dash_rows, stats_rows)
        else:
            rows = stats_rows

    augmenter.augment(breakdown, rows)
    permission_filter.filter_columns_by_permission(user, constraints, rows, goals)

    return rows


@newrelic.agent.function_trace()
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

    permission_filter.filter_columns_by_permission(user, constraints, stats_rows, goals)

    return stats_rows[0]


@newrelic.agent.function_trace()
def counts(level, user, breakdown, constraints, parents, goals):
    helpers.check_constraints_are_supported(constraints)
    target_dimension = constants.get_target_dimension(breakdown)
    parents = helpers.decode_parents(breakdown, parents)
    stats_constraints = helpers.extract_stats_constraints(constraints, breakdown)
    use_publishers_view = should_use_publishers_view(breakdown)

    if target_dimension == constants.StructureDimension.SOURCE:
        """
        We are removing rows of deprecated sources without stats. This can be done only
        after we merge dash rows with stats rows. Because of this special case we must
        compute count in memory.
        """
        queries = dash.dashapi.api_breakdowns.query_async_start(level, user, breakdown, constraints, parents)
        dash_rows = dash.dashapi.api_breakdowns.query_async_get_results(queries, breakdown)
        stats_rows = redshiftapi.api_breakdowns.query_stats_for_rows(
            dash_rows, breakdown, stats_constraints, goals, use_publishers_view=use_publishers_view
        )
        rows = helpers.merge_rows(breakdown, dash_rows, stats_rows)
        augmenter.augment(breakdown, rows)
        augmenter.remove_deprecated_sources_with_no_stats(rows, constraints)
        count_rows = helpers.extract_counts(parents, rows)
        return count_rows

    if target_dimension in constants.DeliveryDimension._ALL:
        """
        We are removing rows without stats in memory after rs returns data.
        Because of this special case we must compute count in memory.
        """
        stats_rows = redshiftapi.api_breakdowns.query_with_background_cache(
            breakdown, stats_constraints, parents, goals, use_publishers_view=use_publishers_view
        )
        augmenter.augment(breakdown, stats_rows)
        count_rows = helpers.extract_counts(parents, stats_rows)
        return count_rows

    should_query_dashapi = helpers.should_query_counts_dashapi(target_dimension)
    if should_query_dashapi:
        queries = dash.dashapi.api_breakdowns.query_counts_async_start(level, user, breakdown, constraints, parents)
        count_rows = dash.dashapi.api_breakdowns.query_counts_async_get_results(queries)
    else:
        count_rows = redshiftapi.api_breakdowns.query_counts(
            breakdown, stats_constraints, parents, goals, use_publishers_view=use_publishers_view
        )
    augmenter.augment_counts(breakdown, count_rows)
    return count_rows


def validate_breakdown_allowed(level, user, breakdown):
    permission_filter.validate_breakdown_by_structure(breakdown)
    permission_filter.validate_breakdown_by_permissions(level, user, breakdown)


def should_use_publishers_view(breakdown):
    return ("publisher_id" in breakdown and "content_ad_id" not in breakdown) or constants.is_placement_breakdown(
        breakdown
    )


@newrelic.agent.function_trace()
def _join_structure_thread(structure_thread):
    # separate function for instrumentation sake
    structure_thread.join()
