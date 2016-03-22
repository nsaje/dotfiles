import logging

from redshift import models, db, helpers
from templatesql import generate_query


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


""" TEST

import datetime
from redshift import models, db, helpers
from redshift.api import query_breakdown

model = models.RSContentAdsModel
breakdown = ['account_id', 'ad_group_id']
constraints = {
    'date_from': datetime.date(2016, 1, 1),
    'date_to': datetime.date(2016, 4, 1),
    'ad_group_id': [890, 1530, 1349, 1172, 885, 1411]
}
r = query_breakdown(model, breakdown, constraints, None, None)

"""