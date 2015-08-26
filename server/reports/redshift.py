from django.db import connections, transaction

STATS_DB_NAME = 'stats'


@transaction.atomic()
def delete_contentadstats(date, ad_group_id, source_id):
    query = 'DELETE FROM contentadstats WHERE TRUNC(%s) = %s AND adgroup_id = %s'
    params = [date.isoformat(), ad_group_id]

    if source_id:
        query = query + ' AND source_id = %s'
        params.append(source_id)

    _execute(query, params)


@transaction.atomic()
def insert_contentadstats(rows):
    if not rows:
        return

    cols = rows[0].keys()

    query = 'INSERT INTO contentadstats %s VALUES %s'
    params = [','.join(cols), ','.join([_get_values_string(row, cols) for row in rows])]

    _execute(query, params)


def _execute(query, params):
    with connections[STATS_DB_NAME].cursor() as cursor:
        cursor.execute(query, params)


def _get_values_string(row, cols):
    return '({})'.format(','.join([str(row[col]) for col in cols]))
