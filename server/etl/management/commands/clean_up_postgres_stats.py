import datetime
import logging

from django.conf import settings

import utils.dates_helper
from etl import maintenance
from etl import redshift
from etl import refresh
from redshiftapi import db
from utils import metrics_compat
from utils.command_helpers import Z1Command

logger = logging.getLogger(__name__)


POSTGRES_KEEP_DAYS = 64


class Command(Z1Command):
    @metrics_compat.timer("etl.clean_up_postgres_stats")
    def handle(self, *args, **options):
        for db_name in settings.STATS_DB_WRITE_REPLICAS_POSTGRES:
            for table in refresh.get_all_views_table_names():
                self._delete_old_data(table, db_name)
                maintenance.vacuum(table, db_name=db_name)
                maintenance.analyze(table, db_name=db_name)

    @staticmethod
    def _delete_old_data(table, db_name):
        date_from = datetime.date(1970, 1, 1)
        date_to = utils.dates_helper.days_before(utils.dates_helper.local_today(), POSTGRES_KEEP_DAYS)
        with db.get_write_stats_cursor(db_name) as c:
            logger.info('Deleting old data from table "%s"', table)
            sql, params = redshift.prepare_date_range_delete_query(table, date_from, date_to, None)
            c.execute(sql, params)
