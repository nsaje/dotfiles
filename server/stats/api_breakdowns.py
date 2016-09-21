from utils import exc
from utils import sort_helper

import dash.models
import dash.campaign_goals

from reports.db_raw_helpers import is_collection

from stats import helpers
from stats import constants
from stats import augmenter
from stats import permission_filter

# expose these helpers as API
from stats.helpers import get_goals
from stats.constraints_helper import prepare_all_accounts_constraints, prepare_account_constraints
from stats.constraints_helper import prepare_campaign_constraints, prepare_ad_group_constraints

import redshiftapi.api_breakdowns
import dash.dashapi.api_breakdowns


# define the API
__all__ = ['query', 'totals', 'validate_breakdown_allowed', 'get_goals',
           'prepare_all_accounts_constraints', 'prepare_account_constraints',
           'prepare_campaign_constraints', 'prepare_ad_group_constraints']


def validate_breakdown_allowed(level, user, breakdown):
    permission_filter.validate_breakdown_by_structure(breakdown)
    permission_filter.validate_breakdown_by_permissions(level, user, breakdown)


def query(level, user, breakdown, constraints, goals, parents, order, offset, limit):
    """
    Get a breakdown report. Data is sourced from dash models and redshift.

    All field names and values in breakdown, constraints, parents and order should
    use valid field names. Field names should match those of used in dash and redshiftapi models.
    """

    helpers.check_constraints_are_supported(constraints)

    target_dimension = constants.get_target_dimension(breakdown)

    order = helpers.extract_order_field(order, target_dimension, goals.primary_goals)
    order = helpers.get_supported_order(order, target_dimension)

    parents = helpers.decode_parents(breakdown, parents)
    stats_constraints = helpers.extract_stats_constraints(constraints, breakdown)

    if helpers.should_query_dashapi_first(order, target_dimension):
        rows = dash.dashapi.api_breakdowns.query(level, breakdown, constraints, parents, order, offset, limit)
        rows = redshiftapi.api_breakdowns.augment(
            rows,
            breakdown,
            stats_constraints,
            goals
        )
    else:
        rows = redshiftapi.api_breakdowns.query(
            breakdown,
            stats_constraints,
            parents,
            goals,
            helpers.extract_rs_order_field(order, target_dimension),
            offset,
            limit)
        if helpers.should_augment_by_dash(target_dimension):
            structure_with_stats = None
            if target_dimension != 'publisher':
                if offset == 0:
                    # when we are loading first page, we need already know everything
                    structure_with_stats = rows
                else:
                    structure_with_stats = redshiftapi.api_breakdowns.query_structure_with_stats(
                        breakdown, stats_constraints)

            rows = dash.dashapi.api_breakdowns.augment(rows, level, breakdown, constraints)
            rows = dash.dashapi.api_breakdowns.query_missing_rows(
                rows, level, breakdown, constraints, parents, order, offset, limit, structure_with_stats)

    augmenter.augment(breakdown, rows)
    augmenter.cleanup(rows, target_dimension, constraints)
    permission_filter.filter_columns_by_permission(user, rows, goals)

    return rows


def totals(user, level, breakdown, constraints, goals):
    helpers.check_constraints_are_supported(constraints)

    stats_rows = redshiftapi.api_breakdowns.query(
            [],
            helpers.extract_stats_constraints(constraints, breakdown),
            None,
            goals,
            None, None, None)

    dash_total_row = dash.dashapi.api_breakdowns.get_totals(level, breakdown, constraints)

    for k, v in dash_total_row.items():
        stats_rows[0][k] = v

    permission_filter.filter_columns_by_permission(user, stats_rows, goals)

    return stats_rows[0]
