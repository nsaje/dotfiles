import copy

from stats import helpers

import redshiftapi.api_breakdowns

"""
Enhancments: futures for database queries
   While RS is loading we can also be loading dash data.

1. get report with ALL columns
2. extra columns get stripped out later


PROBLEM:
  - how to get level data

Example breakdown: [campaign, source]
"""

# TODO handle 'other' rows
# TODO level specific api
# TODO which columns should be queried (what exists per level)

DEFAULT_ORDER = ['-clicks']  # this is level specific


def query(user, breakdown, constraints, breakdown_constraints, order=DEFAULT_ORDER, page=1, page_size=10):
    # TODO page, page_size should be outsorced to view - based on which view, exports have a bigger one

    stats_rows = redshiftapi.api_breakdowns.query(
        breakdown,
        helpers.extract_stats_constraints(constraints),
        breakdown_constraints,
        order or DEFAULT_ORDER,
        page,
        page_size)

    return stats_rows


def get_dash_data(breakdown, stats_data):
    augmented_dimension = breakdown[-1]

    if augmented_dimension == 'source':
        # get all sources that reside in the stats
        pass


def _merge():
    # merge dash and stats rows
    pass


def _augment(breakdown, stats_rows, dash_rows):
    # we augment with the last level data
    # add names, stats, constants etc to rows
    pass


def _secure():
    # remove columns without permission
    pass