import datetime
import logging
import influx

from utils.command_helpers import ExceptionCommand
import utils.dates_helper
from redshiftapi import db

from etl import maintenance
from etl import redshift


logger = logging.getLogger(__name__)


SUPPLY_STATS_KEEP_DAYS = 35
SUPPLY_STATS_TABLE = "supply_stats"


class Command(ExceptionCommand):
    @influx.timer("etl.clean_up_supply_stats")
    def handle(self, *args, **options):
        self._delete_old_data(SUPPLY_STATS_TABLE)
        maintenance.vacuum(SUPPLY_STATS_TABLE, delete_only=True)
        maintenance.analyze(SUPPLY_STATS_TABLE)

    @staticmethod
    def _delete_old_data(table):
        date_from = datetime.date(1970, 1, 1)
        date_to = utils.dates_helper.days_before(utils.dates_helper.local_today(), SUPPLY_STATS_KEEP_DAYS)
        with db.get_write_stats_cursor() as c:
            logger.info('Deleting old data from table "%s"', table)
            sql, params = redshift.prepare_date_range_delete_query(table, date_from, date_to, None)
            c.execute(sql, params)
