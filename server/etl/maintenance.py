import backtosql
import logging

from redshiftapi import db


logger = logging.getLogger(__name__)


def _execute_query(db_name, query, *params):
    with db.get_stats_cursor(db_name) as c:
        c.execute(query, params)


def vacuum(table, delete_only=False, db_name=None):
    logger.info('Starting VACUUM table %s', table)
    if delete_only:
        _execute_query(db_name, 'VACUUM DELETE ONLY {}'.format(table))
    else:
        _execute_query(db_name, 'VACUUM {}'.format(table))
    logger.info('Finished VACUUM table %s', table)


def analyze(table, db_name=None):
    logger.info('Starting ANALYZE table %s', table)
    _execute_query(db_name, 'ANALYZE {}'.format(table))
    logger.info('Finished ANALYZE table %s', table)


def truncate(table, db_name=None):
    logger.info('Starting TRUNCATE table %s', table)
    _execute_query(db_name, 'TRUNCATE {}'.format(table))
    logger.info('Finished TRUNCATE table %s', table)


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
