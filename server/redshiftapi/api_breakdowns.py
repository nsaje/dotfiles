import copy
import backtosql
from backtosql.helpers import printsql

from redshiftapi import models
from redshiftapi import db
from redshiftapi import queries
from redshiftapi import helpers

from dash import breakdown_helpers
from utils import exc

# TODO breakdown helpers have a general mapping in dash/breakdown_helpers
# and redshiftapi internal mapping that happens when we are converting to
# real columns


def query(breakdown, constraints, breakdown_constraints, order, page, page_size):
    # returns a collection of rows that are dicts
    # TODO supported order len == 1 -> breakdown levels 1 and 2 don't go without it

    model = models.RSContentAdStats

    # first translate fields into what our code understands
    breakdown = model.copy_and_translate_breakdown(breakdown)
    constraints = model.copy_and_translate_dict(constraints)
    breakdown_constraints = model.copy_and_translate_dicts(breakdown_constraints)

    query, params = _prepare_query(model, breakdown, constraints, breakdown_constraints, order, page, page_size)

    # execute the query
    with db.get_stats_cursor() as cursor:
        # DEBUG info
        printsql(query, params, cursor)

        cursor.execute(query, params)
        # TODO fetchall, namedtuplefetchall? - what is more appropripate
        results = db.dictfetchall(cursor)

    return results


def _prepare_query(model, breakdown, constraints, breakdown_constraints,
                   order, page, page_size):

    time_dimension = breakdown_helpers.get_time(breakdown)
    if time_dimension:
        # should also cover when len(breakdown) == 4
        return queries.prepare_time_top_rows(model, time_dimension, breakdown, constraints, breakdown_constraints,
                                             order, page, page_size)

    if len(breakdown) == 2:
        return queries.prepare_lvl1_top_rows(model, breakdown, constraints, breakdown_constraints,
                                             order, page, page_size)

    elif len(breakdown) == 3:
        return queries.prepare_lvl2_top_rows(model, breakdown, constraints, breakdown_constraints,
                                             order, page, page_size)

    raise exc.InvalidBreakdownError()