import copy
import backtosql
from backtosql.q import Q
from backtosql.helpers import printsql

from redshiftapi import models
from redshiftapi import db


def query(breakdown, constraints, breakdown_constraints, order, page, page_size):
    # returns a collection of rows that are dicts
    # TODO supported order len == 1 -> breakdown levels 1 and 2 don't go without it

    assert len(order) == 1
    query, params = _prepare_query(
        models.RSContentAdStats,
        breakdown, constraints, breakdown_constraints, order, page, page_size)

    with db.get_cursor() as cursor:
        cursor.execute(query, params)
        results = cursor.dictfetchall()

    return results


def _prepare_query(model,
                   breakdown, constraints, breakdown_constraints,
                   order, page, page_size):

    # TODO prepare_query could be template name specific
    # its easier to link data needed
    # pick template name more explicitly
    # template_name -> context = specific
    # view might also be, but otherwise it has a different selection logics
    # than template_name and context

    # also note - special templates when time involved - as it does not
    # need to be shortened, because that can be done with date adjustment

    template_name = model.get_best_query_template(
        breakdown, constraints)

    constraints = _prepare_constraints(model, constraints, breakdown_constraints)

    context = {
        'view': model.get_best_view(breakdown),
        'constraints': constraints,
        'breakdown_constraints': breakdown_constraints,
        'breakdown': model.get_breakdown(breakdown),
        'aggregates': model.get_aggregates(),
        'order': model.select_order(order),
        'offset': (page - 1) * page_size,
        'limit': page * page_size, # page is 1-based
    }

    params = constraints.get_params()

    query = backtosql.generate_sql(template_name, context)

    print 'QUERY', query
    print 'PARAMS', params

    return query, params


def _prepare_constraints(model, constraints, breakdown_constraints):

    q = Q(model, **constraints)

    return q


def _prepare_breakdown_constraints(model, breakdown_constraints):
    if breakdown_constraints:
        bq = Q(model, **breakdown_constraints[0])

        for branch in breakdown_constraints[1:]:
            bq |= Q(model, **branch)

        return bq
    return None