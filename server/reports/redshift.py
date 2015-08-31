from itertools import repeat
from reports.db_raw_helpers import dictfetchall

from django.db import connections

STATS_DB_NAME = 'stats'


def delete_contentadstats(date, ad_group_id, source_id):
    cursor = _get_cursor()

    query = 'DELETE FROM contentadstats WHERE TRUNC(datetime) = %s AND adgroup_id = %s'
    params = [date.isoformat(), ad_group_id]

    if source_id:
        query = query + ' AND source_id = %s'
        params.append(source_id)

    cursor.execute(query, params)
    cursor.close()


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


def sum_contentadstats():
    query = 'SELECT SUM(impressions) as impressions, SUM(visits) as visits FROM contentadstats'

    cursor = _get_cursor()
    cursor.execute(query, [])

    cursor.close()
    return dictfetchall(cursor)


def _get_cursor():
    return connections[STATS_DB_NAME].cursor()


def _get_row_string(cursor, cols, row):
    template_string = '(' + ','.join(repeat('%s', len(cols))) + ')'
    return cursor.mogrify(template_string, [row[col] for col in cols])
