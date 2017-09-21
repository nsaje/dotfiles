import backtosql
import influx
import logging

from redshiftapi import db
from etl import helpers


logger = logging.getLogger(__name__)


def _execute_query(query, *params):
    with db.get_stats_cursor() as c:
        c.execute(query, params)


def vacuum(table, delete_only=False):
    logger.info('Starting VACUUM table %s', table)
    if delete_only:
        _execute_query('VACUUM DELETE ONLY {}'.format(table))
    else:
        _execute_query('VACUUM {}'.format(table))
    logger.info('Finished VACUUM table %s', table)


def analyze(table):
    logger.info('Starting ANALYZE table %s', table)
    _execute_query('ANALYZE {}'.format(table))
    logger.info('Finished ANALYZE table %s', table)


def truncate(table):
    logger.info('Starting TRUNCATE table %s', table)
    _execute_query('TRUNCATE {}'.format(table))
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


def crossvalidate_traffic(date_from, date_to):
    """
    NOTE: It is recommended that you run this validation when ETL is not running, otherwise you will
    most certanly vitness various discrepancies.
    """

    params = helpers.get_local_multiday_date_context(date_from, date_to)
    sql = backtosql.generate_sql('etl_crossvalidate_traffic.sql', None)

    with db.get_stats_cursor() as c:
        c.execute(sql, params)

        result = db.namedtuplefetchall(c)[0]

    date_range = str((date_to - date_from).days)

    influx.gauge('etl.crossvalidation.diff_s_ca_clicks', result.diff_s_ca_clicks, date_range=date_range)
    influx.gauge('etl.crossvalidation.diff_s_mv_clicks', result.diff_s_mv_clicks, date_range=date_range)
    influx.gauge('etl.crossvalidation.diff_s_ca_impressions', result.diff_s_ca_impressions, date_range=date_range)
    influx.gauge('etl.crossvalidation.diff_s_mv_impressions', result.diff_s_mv_impressions, date_range=date_range)
    influx.gauge('etl.crossvalidation.diff_s_ca_spend_micro', result.diff_s_ca_spend_micro, date_range=date_range)
    influx.gauge('etl.crossvalidation.diff_s_mv_spend_micro', result.diff_s_mv_spend_micro, date_range=date_range)
    influx.gauge('etl.crossvalidation.diff_s_ca_data_spend_micro', result.diff_s_ca_data_spend_micro,
                 date_range=date_range)
    influx.gauge('etl.crossvalidation.diff_s_mv_data_spend_micro', result.diff_s_mv_data_spend_micro,
                 date_range=date_range)
    influx.gauge('etl.crossvalidation.diff_ca_mv_effective_cost_nano', result.diff_ca_mv_effective_cost_nano,
                 date_range=date_range)

    influx.gauge('etl.crossvalidation.spend_nano', result.spend_nano, date_range=date_range)
    influx.gauge('etl.crossvalidation.effective_cost_nano', result.effective_cost_nano, date_range=date_range)
    influx.gauge('etl.crossvalidation.overspend_nano', result.overspend_nano, date_range=date_range)

    return result
