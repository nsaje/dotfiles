from redshiftapi import db
from redshiftapi import models
from redshiftapi import queries

from stats import constants
from utils import exc


def query(breakdown, constraints, breakdown_constraints, order, offset, limit):
    # returns a collection of rows that are dicts

    model = models.RSContentAdStats

    query, params = _prepare_query(model, breakdown, constraints, breakdown_constraints, order, offset, limit)

    with db.get_stats_cursor() as cursor:
        cursor.execute(query, params)
        results = db.dictfetchall(cursor)

    return results


def _prepare_query(model, breakdown, constraints, breakdown_constraints,
                   order, offset, limit):

    default_context = model.get_default_context(breakdown, constraints, breakdown_constraints,
                                                order, offset, limit)

    time_dimension = constants.get_time_dimension(breakdown)
    if time_dimension:
        # should also cover the case for len(breakdown) == 4 because in that case time dimension should be the last one
        return queries.prepare_time_top_rows(model, time_dimension, default_context, constraints, offset, limit)

    if len(breakdown) == 2:
        return queries.prepare_lvl1_top_rows(default_context)

    elif len(breakdown) == 3:
        return queries.prepare_lvl2_top_rows(default_context)

    raise exc.InvalidBreakdownError("Selected breakdown is not supported {}".format(breakdown))
