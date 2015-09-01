from itertools import repeat
from reports.db_raw_helpers import dictfetchall

from django.db import connections

from utils.statsd_helper import statsd_timer

STATS_DB_NAME = 'stats'


@statsd_timer('reports.redshift', 'delete_contentadstats')
def delete_contentadstats(date, ad_group_id, source_id):
    cursor = _get_cursor()

    query = 'DELETE FROM contentadstats WHERE TRUNC(date) = %s AND adgroup_id = %s'
    params = [date.isoformat(), ad_group_id]

    if source_id:
        query = query + ' AND source_id = %s'
        params.append(source_id)

    cursor.execute(query, params)
    cursor.close()


@statsd_timer('reports.redshift', 'insert_contentadstats')
def insert_contentadstats(rows):
    if not rows:
        return

    cursor = _get_cursor()

    cols = rows[0].keys()

    query = 'INSERT INTO contentadstats ({cols}) VALUES {rows}'.format(
        cols=','.join(cols),
        rows=','.join(_get_row_string(cursor, cols, row) for row in rows))

    cursor.execute(query, [])
    cursor.close()


@statsd_timer('reports.redshift', 'sum_contentadstats')
def sum_contentadstats():
    query = 'SELECT SUM(impressions) as impressions, SUM(visits) as visits FROM contentadstats'

    cursor = _get_cursor()
    cursor.execute(query, [])

    result = dictfetchall(cursor)

    cursor.close()
    return result[0]


@statsd_timer('reports.redshift', 'vacuum_contentadstats')
def vacuum_contentadstats():
    query = 'VACUUM FULL contentadstats'

    cursor = _get_cursor()
    cursor.execute(query, [])

    cursor.close()


def _get_cursor():
    return connections[STATS_DB_NAME].cursor()


def _get_row_string(cursor, cols, row):
    template_string = '(' + ','.join(repeat('%s', len(cols))) + ')'
    return cursor.mogrify(template_string, [row[col] for col in cols])
