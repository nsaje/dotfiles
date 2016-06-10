from django.db import connections
from django.conf import settings


def _execute_query(query, *params):
    with connections[settings.STATS_DB_NAME].cursor() as c:
        c.execute(query, params)


def vacuum_and_analyze(table):
    _execute_query('VACUUM {}'.format(table))
    _execute_query('ANALYZE {}'.format(table))
