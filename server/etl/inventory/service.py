import logging
import backtosql

from redshiftapi import db
from etl import maintenance


logger = logging.getLogger(__name__)


TABLE_NAME = 'mv_inventory'


def refresh_inventory_data(date_from, date_to, skip_vacuum=False):
    sql = backtosql.generate_sql('etl_aggregate_inventory_data.sql', None)

    with db.get_stats_cursor() as c:
        maintenance.truncate(TABLE_NAME)
        logger.info('Starting materialization of table %s', TABLE_NAME)
        c.execute(sql, {
            'date_from': date_from,
            'date_to': date_to,
        })
        logger.info('Finished materialization of table %s', TABLE_NAME)
        maintenance.vacuum(TABLE_NAME)
        maintenance.analyze(TABLE_NAME)
