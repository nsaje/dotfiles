from redshift import models
from redshift.engine import RSCursor, RSQuery

from django.conf import settings
from django.db import connections


def query(breakdown, constraints, order, page):

    # should be class not instance
    model = models.ContentAdsModel()

    qx = RSQuery('common_lvl1.sql')
    sql = qx.generate(
        model.get_breakdown_columns(breakdown), model.get_aggregate_columns(),
        constraints, order, page)
    print sql
    pass


import datetime
from django.conf import settings
from django.db import connections
from redshift import models
from redshift.engine import RSCursor, RSBreakdownQuery

m = models.ContentAdsModel()
q = RSBreakdownQuery('common_lvl1.sql')
constraints = {'ad_group_id': [1, 2, 3],
               'date_from': datetime.datetime(2016, 1, 1),
               'date_to': datetime.datetime(2016, 2, 2)}

sql = q.generate(
    m.get_breakdown_columns(['account_id']),
    m.get_aggregate_columns(),
    constraints,
    None,
    None,
    view='contentadstats')

with RSCursor(connections[settings.STATS_DB_NAME].cursor()) as c:
    c.execute(sql, constraints)
    result = c.dictfetchall()
