import copy
import backtosql
import backtosql

from redshiftapi import models
from redshiftapi import db
from redshiftapi import queries

from stats import constants
from utils import exc


def query(breakdown, constraints, breakdown_constraints, order, offset, limit):
    # returns a collection of rows that are dicts

    model = models.RSContentAdStats

    query, params = _prepare_query(model, breakdown, constraints, breakdown_constraints, order, offset, limit)

    with db.get_stats_cursor() as cursor:

        # FIXME Info for debugging
        backtosql.printsql(query, params, cursor)

        cursor.execute(query, params)

        results = db.dictfetchall(cursor)

    return results


def _prepare_query(model, breakdown, constraints, breakdown_constraints,
                   order, offset, limit):

    time_dimension = constants.get_time_dimension(breakdown)
    if time_dimension:
        # should also cover the case for len(breakdown) == 4
        # because in that case time dimension should be the
        # last one
        return queries.prepare_time_top_rows(model, time_dimension, breakdown, constraints, breakdown_constraints,
                                             order, offset, limit)

    if len(breakdown) == 2:
        return queries.prepare_lvl1_top_rows(model, breakdown, constraints, breakdown_constraints,
                                             order, offset, limit)

    elif len(breakdown) == 3:
        return queries.prepare_lvl2_top_rows(model, breakdown, constraints, breakdown_constraints,
                                             order, offset, limit)

    raise exc.InvalidBreakdownError("Selected breakdown is not supported {}".format(breakdown))
