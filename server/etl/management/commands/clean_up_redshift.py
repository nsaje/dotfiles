import datetime
import logging

import influx

import utils.dates_helper
from etl import maintenance
from etl import redshift
from redshiftapi import db
from utils.command_helpers import Z1Command

logger = logging.getLogger(__name__)


CONFIG = [{"table_name": "supply_stats", "keep_days": 31}, {"table_name": "stats", "keep_days": 93}]


class Command(Z1Command):
    @influx.timer("etl.clean_up_redshift")
    def handle(self, *args, **options):
        for config in CONFIG:
            table_name = config["table_name"]
            keep_days = config["keep_days"]
            self._delete_old_data(table_name, keep_days)
            maintenance.vacuum(table_name, delete_only=True)
            maintenance.analyze(table_name)

    @staticmethod
    def _delete_old_data(table, keep_days):
        date_from = datetime.date(1970, 1, 1)
        date_to = utils.dates_helper.days_before(utils.dates_helper.local_today(), keep_days)
        with db.get_write_stats_cursor() as c:
            logger.info('Deleting old data from table "%s"', table)
            sql, params = redshift.prepare_date_range_delete_query(table, date_from, date_to, None)
            c.execute(sql, params)
