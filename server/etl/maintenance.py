import backtosql

from redshiftapi import db


def _execute_query(query, *params):
    with db.get_stats_cursor() as c:
        c.execute(query, params)


def vacuum_and_analyze(table):
    _execute_query('VACUUM {}'.format(table))
    _execute_query('ANALYZE {}'.format(table))


def cluster_disk_usage():
    sql = backtosql.generate_sql('maintenance_cluster_disk_usage.sql', None)

    with db.get_stats_cursor() as c:
        c.execute(sql)

        result = db.namedtuplefetchall(c)

    return result[0]


def cluster_tables_disk_usage():
    sql = backtosql.generate_sql('maintenance_tables_disk_usage.sql', None)

    with db.get_stats_cursor() as c:
        c.execute(sql)

        result = db.namedtuplefetchall(c)

    return result
