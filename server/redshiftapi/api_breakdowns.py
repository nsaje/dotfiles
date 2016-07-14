from redshiftapi import db
from redshiftapi import models
from redshiftapi import queries
from redshiftapi import postprocess

from stats import constants
from utils import exc


def query(breakdown, constraints, breakdown_constraints, conversion_goals, order, offset, limit):
    # returns a collection of rows that are dicts

    model = models.MVMaster(conversion_goals)

    query, params = _prepare_query(model, breakdown, constraints, breakdown_constraints,
                                   order, offset, limit)

    with db.get_stats_cursor() as cursor:
        cursor.execute(query, params)
        rows = db.dictfetchall(cursor)

        empty_row = db.get_empty_row_dict(cursor.description)

    _post_process(rows, empty_row, breakdown, constraints, breakdown_constraints)

    return rows


def _prepare_query(model, breakdown, constraints, breakdown_constraints,
                   order, offset, limit):

    default_context = model.get_default_context(breakdown, constraints, breakdown_constraints, order, offset, limit)

    time_dimension = constants.get_time_dimension(breakdown)
    if time_dimension:
        # should also cover the case for len(breakdown) == 4 because in that case time dimension should be the last one
        return queries.prepare_time_top_rows(model, time_dimension, default_context, constraints)

    if 2 <= len(breakdown) <= 3:
        return queries.prepare_breakdown_struct_delivery_top_rows(default_context)

    raise exc.InvalidBreakdownError("Selected breakdown is not supported {}".format(breakdown))


def _post_process(rows, empty_row, breakdown, constraints, breakdown_constraints):
    time_dimension = constants.get_time_dimension(breakdown)

    if time_dimension:
        postprocess.postprocess_time_dimension(time_dimension, rows, empty_row,
                                               breakdown, constraints, breakdown_constraints)
