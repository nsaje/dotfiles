from redshiftapi import db


def _execute_query(query, *params):
    with db.get_stats_cursor() as c:
        c.execute(query, params)


def vacuum_and_analyze(table):
    _execute_query('VACUUM {}'.format(table))
    _execute_query('ANALYZE {}'.format(table))
