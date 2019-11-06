import backtosql
from redshiftapi import db
from utils import zlogging

logger = zlogging.getLogger(__name__)


def _execute_query(db_name, query, *params):
    with db.get_stats_cursor(db_name) as c:
        c.execute(query, params)


def vacuum(table, delete_only=False, to=None, db_name=None):
    logger.info("Starting VACUUM table", table=table)
    if delete_only:
        _execute_query(db_name, "VACUUM DELETE ONLY {}".format(table))
    else:
        if to:
            _execute_query(db_name, "VACUUM {} TO {} PERCENT".format(table, to))
        else:
            _execute_query(db_name, "VACUUM {}".format(table))
    logger.info("Finished VACUUM table", table=table)


def analyze(table, db_name=None):
    logger.info("Starting ANALYZE table", table=table)
    _execute_query(db_name, "ANALYZE {}".format(table))
    logger.info("Finished ANALYZE table", table=table)


def truncate(table, db_name=None):
    logger.info("Starting TRUNCATE table", table=table)
    _execute_query(db_name, "TRUNCATE {}".format(table))
    logger.info("Finished TRUNCATE table", table=table)


def stats_min_date():
    logger.info("Querying earliest date in stats table")
    sql = "select min(date) from stats;"
    with db.get_stats_cursor() as c:
        c.execute(sql)
        result = c.fetchone()[0]
    logger.info("Finished querying earliest date in stats table")
    return result


def cluster_disk_usage():
    sql = backtosql.generate_sql("maintenance_cluster_disk_usage.sql", None)

    with db.get_stats_cursor() as c:
        c.execute(sql)

        result = db.namedtuplefetchall(c)

    return result[0]


def cluster_tables_disk_usage():
    sql = backtosql.generate_sql("maintenance_tables_disk_usage.sql", None)

    with db.get_stats_cursor() as c:
        c.execute(sql)

        result = db.namedtuplefetchall(c)

    return result
