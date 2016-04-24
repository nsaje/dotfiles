import backtosql

from redshiftapi import models
from redshiftapi import db


def query(breakdown, constraints, order, page):

    query, params = _prepare_query(models.RSContentAdStats, breakdown, constraints, order, page)

    with db.get_cursor() as cursor:
        cursor.execute(query, params)
        results = cursor.dictfetchall()

    return results


def _prepare_query(model, breakdown, constraints, order, page):
    template_name = models.RSContentAdStats.get_best_query_template(breakdown, constraints)
    context = models.RSContentAdStats.get_default_context(breakdown, constraints, order, page)
    params = context['params']

    query = backtosql.generate_sql(template_name, context)

    return query, params