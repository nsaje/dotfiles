import logging

from redshift import models, db, helpers
from backtosql import generate_query


logger = logging.getLogger(__name__)


def query_breakdown(model, breakdown, constraints, order, page, exaggerate=True):
    # exaggerate :: overblow the page sizes if you find that suitable
    # order :: if order is not available - let it know that it needs to do it in upper layer

    # find in cache and return if present

    logger.debug("Breakdown page not found in cache")
    # TODO log selected view, page size

    sql = generate_query(model.get_query_template(), {
        'view': model.get_view(breakdown),
        'breakdowns': model.select_columns(breakdown),
        'aggregates': model.select_columns(group=models.ColumnGroup.AGGREGATES),
        'order': order,
        'page': page,
    })

    logger.debug("Executing SQL in RS:", helpers.printsql(sql))
    with db.RSCursor() as c:
        c.execute(sql, constraints)
        result = c.fetchall()

    logger.debug("Putting page into cache")
    # put into cache
    # select subpage

    return result
