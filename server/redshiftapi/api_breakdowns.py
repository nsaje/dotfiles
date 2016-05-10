import backtosql
from backtosql.q import Q

from redshiftapi import models
from redshiftapi import db


def query(breakdown, constraints, breakdown_constraints, order, page, page_size):
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

    template_name = model.get_best_query_template(
        breakdown, constraints)

    constraints = _prepare_constraints(model, constraints, breakdown_constraints)
    context = {
        'view': model.get_best_view(breakdown),
        'constraints': constraints,
        'breakdown': model.get_breakdown(breakdown),
        'aggregates': model.get_aggregates(),
        'order': model.select_order(order),
        'offset': (page - 1) * page_size,
        'limit': page * page_size, # page is 1-based
    }

    params = constraints.get_params()

    query = backtosql.generate_sql(template_name, context)

    return query, params


def _prepare_constraints(model, constraints, breakdown_constraints):
    q = Q(model, **constraints)

    if breakdown_constraints:
        bq = Q(model, **breakdown_constraints[0])
        print breakdown_constraints[0]

        for branch in breakdown_constraints[1:]:
            tq = Q(model, **branch)

            bq |= tq

        q &= bq
    return q