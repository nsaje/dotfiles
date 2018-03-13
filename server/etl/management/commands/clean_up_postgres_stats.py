import datetime
import logging
import influx

from utils.command_helpers import ExceptionCommand
import utils.dates_helper
from redshiftapi import db

from etl import maintenance
from etl import refresh_k1
from etl import materialize_views

from django.conf import settings


logger = logging.getLogger(__name__)


POSTGRES_KEEP_DAYS = 64


class Command(ExceptionCommand):
    @influx.timer('etl.clean_up_postgres_stats')
    def handle(self, *args, **options):
        for db_name in settings.STATS_DB_WRITE_REPLICAS_POSTGRES:
            for table in refresh_k1.get_all_views_table_names():
                self._delete_old_data(table, db_name)
                maintenance.vacuum(table, db_name=db_name)
                maintenance.analyze(table, db_name=db_name)

    @staticmethod
    def _delete_old_data(table, db_name):
        date_from = datetime.date(1970, 1, 1)
        date_to = utils.dates_helper.days_before(utils.dates_helper.local_today(), POSTGRES_KEEP_DAYS)
        with db.get_write_stats_cursor(db_name) as c:
            logger.info('Deleting old data from table "%s"', table)
            sql, params = materialize_views.prepare_date_range_delete_query(table, date_from, date_to, None)
            c.execute(sql, params)
