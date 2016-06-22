import copy

from utils import exc
from utils import sort_helper

from stats import helpers
from stats import constants
from stats import augmenter

import redshiftapi.api_breakdowns

# TODO handle 'other' rows
# TODO level specific api (different columns, order)
# TODO which columns should be queried/returned (what exists per level, permissions)
# TODO if sort is in dash than this should be sorted by dash data (fetch before)
# TODO use constants for other dimensions like age, gender etc


def query(user, breakdown, constraints, breakdown_page,
          order, offset, limit):

    validate_breakdown(breakdown)

    rows = redshiftapi.api_breakdowns.query(
        helpers.extract_stats_breakdown(breakdown),
        helpers.extract_stats_constraints(constraints),
        helpers.extract_stats_breakdown_constraints(breakdown, breakdown_page),
        order,
        offset,
        limit)

    target_dimension = constants.get_target_dimension(breakdown)

    augmenter.augment(breakdown, rows, target_dimension)
    augmenter.filter_columns_by_permission(user, rows)

    rows = sort_helper.sort_results(rows, helpers.extract_order_fields(order, breakdown))

    return rows


def validate_breakdown(breakdown):

    base = constants.get_base_dimension(breakdown)
    if not base:
        raise exc.InvalidBreakdownError("Breakdown requires at least 1 dimension")

    clean_breakdown = [base]
    structure = constants.get_structure_dimension(breakdown)
    if structure:
        clean_breakdown.append(structure)

    delivery = constants.get_delivery_dimension(breakdown)
    if delivery:
        clean_breakdown.append(delivery)

    time = constants.get_time_dimension(breakdown)
    if time:
        clean_breakdown.append(time)

    unsupperted_breakdowns = set(breakdown) - set(clean_breakdown)
    if unsupperted_breakdowns:
        raise exc.InvalidBreakdownError("Unsupported breakdowns {}".format(unsupperted_breakdowns))

    if breakdown != clean_breakdown:
        raise exc.InvalidBreakdownError("Wrong breakdown order")
