import copy

from utils import exc

from stats import helpers
from stats import constants

import redshiftapi.api_breakdowns

# TODO handle 'other' rows
# TODO level specific api (different columns, order)
# TODO which columns should be queried/returned (what exists per level, permissions)

DEFAULT_ORDER = '-clicks'  # this is level specific


def query(user, breakdown, constraints, breakdown_constraints,
          order=DEFAULT_ORDER, page=1, page_size=10):
    # TODO if sort is in dash than this should be sorted by dash data (fetch before)

    validate_breakdown(breakdown)

    stats_rows = redshiftapi.api_breakdowns.query(
        breakdown,
        helpers.extract_stats_constraints(constraints),
        breakdown_constraints,
        order or DEFAULT_ORDER,
        page,
        page_size)

    target_dimension = constants.get_target_dimension(breakdown)
    helpers.augment(stats_rows, target_dimension)

    return stats_rows


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
