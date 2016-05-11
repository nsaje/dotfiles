import copy
from stats import constants
from reports.db_raw_helpers import extract_obj_ids

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

DEFAULT_ORDER = ['-clicks']  # this is level specific


# helpers
def _replace_key(d, old_key_name, new_key_name, new_value):
    if old_key_name in d:
        d[new_key_name] = new_value
        del d[old_key_name]


def query_base(user, breakdown, constraints, order, page, page_size):
    assert len(breakdown) == 1

    # TODO use query_breakdown to query data
    # TODO use table.py for this

    totals = None
    stats_rows = []

    report = {
        'rows': rows,
        'totals': totals,
    }

    return report


def query_breakdown(user, breakdown, constraints, breakdown_constraints,
                    order=DEFAULT_ORDER, page=1, page_size=10):
    # TODO page, page_size should be outsorced - based on which view
    # exports have a bigger one
    rows = []

    if not order:
        order = DEFAULT_ORDER

    stats_rows = redshiftapi.api_breakdowns.query(
        breakdown,
        get_rs_constraints(constraints),
        breakdown_constraints,
        order, page, page_size)

    return stats_rows


def get_dash_data(breakdown, stats_data):
    augmented_dimension = breakdown[-1]

    if augmented_dimension == 'source':
        # get all sources that reside in the stats
        pass


def get_rs_constraints(constraints):
    # TODO should this be a responsibility of redshiftsapi module? probably so

    # responsibility of stats as RS doesn't know about
    # some parameters

    # make a copy so that we don't change other references to this dict
    # came into because keys need to be changed (start_date, end_date)

    constraints = copy.copy(constraints)
    del constraints['show_archived']

    # replace values with ids
    constraints = extract_obj_ids(constraints)

    objs = ['account', 'campaign', 'ad_group', 'content_ad', 'source']
    for o in objs:
        if o in constraints:
            _replace_key(constraints, o + '_id', o, constraints[o])

    return constraints


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