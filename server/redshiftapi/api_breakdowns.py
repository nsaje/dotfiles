import copy
import backtosql
from backtosql.q import Q
from backtosql.helpers import printsql

from redshiftapi import models
from redshiftapi import db
from redshiftapi import queries


def query(breakdown, constraints, breakdown_constraints, order, page, page_size):
    # returns a collection of rows that are dicts
    # TODO supported order len == 1 -> breakdown levels 1 and 2 don't go without it

    assert len(order) == 1

    model = models.RSContentAdStats

    # first translate fields into what our code understands
    breakdown = model.translate_breakdown(breakdown)
    constraints = model.translate_dict(constraints)
    breakdown_constraints = model.translate_dicts(breakdown_constraints)

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

    # also note - special templates when time involved - as it does not
    # need to be shortened, because that can be done with date adjustment
    if len(breakdown) == 2:
        return queries.prepare_generic_lvl1(model, breakdown, constraints, breakdown_constraints,
                                     order, page, page_size)
    elif len(breakdown) == 3:
        return queries.prepare_generic_lvl2(model, breakdown, constraints, breakdown_constraints,
                                     order, page, page_size)
    elif len(breakdown) == 4:
        return queries.prepare_generic_lvl3(model, breakdown, constraints, breakdown_constraints,
                                     order, page, page_size)
    raise NotImplementedError()