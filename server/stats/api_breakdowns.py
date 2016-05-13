import copy

from stats import helpers

import redshiftapi.api_breakdowns

# TODO handle 'other' rows
# TODO level specific api
# TODO which columns should be queried (what exists per level)

DEFAULT_ORDER = ['-clicks']  # this is level specific


def query(user, breakdown, constraints, breakdown_constraints, order=DEFAULT_ORDER, page=1, page_size=10):
    # TODO page, page_size should be outsorced to view - based on which view, exports have a bigger one
    # TODO if sort is in dash than this should be sorted by dash data (fetch before)

    stats_rows = redshiftapi.api_breakdowns.query(
        breakdown,
        helpers.extract_stats_constraints(constraints),
        breakdown_constraints,
        order or DEFAULT_ORDER,
        page,
        page_size)

    helpers.augment(stats_rows)
    _secure(stats_rows)

    return stats_rows


def _secure(stats_rows):
    # remove columns without permission
    return stats_rows