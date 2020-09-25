import datetime

from django.db import connection

import utils.dates_helper
from utils import zlogging
from utils.command_helpers import Z1Command

logger = zlogging.getLogger(__name__)

HISTORY_DATA_KEEP_DAYS = 14
PARTITION_CHECK_DAYS = 2


class Command(Z1Command):
    def handle(self, *args, **options):
        utc_today = utils.dates_helper.utc_today().date()
        logger.info("Creating new dash_historystacktrace partitions")
        self._create_new_partitions(utc_today)

        logger.info("Deleting old dash_historystacktrace partitions")
        self._delete_old_partitions(utc_today)

    def _create_new_partitions(self, today):
        cursor = connection.cursor()
        sql = """
            CREATE TABLE IF NOT EXISTS
                dash_historystacktrace_{date_postfix}
            PARTITION OF
                dash_historystacktrace
            FOR VALUES FROM ('{date_from}') TO ('{date_to}');
        """

        for i in range(1, PARTITION_CHECK_DAYS + 1):
            date_from = today + datetime.timedelta(i)
            date_to = today + datetime.timedelta(i + 1)
            cursor.execute(sql.format(date_postfix=date_from.strftime("%Y%m%d"), date_from=date_from, date_to=date_to))

    def _delete_old_partitions(self, today):
        cursor = connection.cursor()
        sql = "DROP TABLE IF EXISTS dash_historystacktrace_{date_postfix};"

        for i in range(1, PARTITION_CHECK_DAYS + 1):
            date = today - datetime.timedelta(HISTORY_DATA_KEEP_DAYS + i)
            cursor.execute(sql.format(date_postfix=date.strftime("%Y%m%d")))
