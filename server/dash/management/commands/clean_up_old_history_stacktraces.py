import datetime

import retrying
from django.db import connection
from django.db.utils import OperationalError
from django.db.utils import ProgrammingError

import utils.dates_helper
from utils import zlogging
from utils.command_helpers import Z1Command

logger = zlogging.getLogger(__name__)

HISTORY_DATA_KEEP_DAYS = 7
PARTITION_CHECK_DAYS = 2


class Command(Z1Command):
    def add_arguments(self, parser):
        parser.add_argument(
            "--delete-partition", dest="delete_partition", help="Delete a single history stacktraces partition"
        )

    def handle(self, *args, **options):
        delete_partition = options.get("delete_partition")

        if delete_partition is not None:
            logger.info("Deleting old dash_historystacktrace partition: %s", delete_partition)
            cursor = connection.cursor()
            cursor.execute("SET lock_timeout TO '2s';")
            self.delete_partition(cursor, delete_partition)
        else:
            self.daily_run()

    def daily_run(self):
        utc_today = utils.dates_helper.utc_today()
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
        cursor.execute("SET lock_timeout TO '2s';")

        for i in range(1, PARTITION_CHECK_DAYS + 1):
            date = today - datetime.timedelta(HISTORY_DATA_KEEP_DAYS + i)
            partition_name = "dash_historystacktrace_{date_postfix}".format(date_postfix=date.strftime("%Y%m%d"))
            self.delete_partition(cursor, partition_name)

    def delete_partition(self, cursor, partition_name):
        self._detach_partition_with_retry(cursor, partition_name)
        cursor.execute(f"DROP TABLE IF EXISTS {partition_name};")

    @retrying.retry(
        retry_on_exception=lambda e: isinstance(e, OperationalError)
        and "canceling statement due to lock timeout" in str(e)
        or "deadlock detected" in str(e),
        stop_max_attempt_number=50,
        wait_exponential_multiplier=1000,
        wait_exponential_max=10000,
    )
    def _detach_partition_with_retry(self, cursor, partition_name):
        try:
            cursor.execute(f"ALTER TABLE dash_historystacktrace DETACH PARTITION IF EXISTS {partition_name};")
        except ProgrammingError:
            # skipping due to non-existing partition
            pass
        except OperationalError as e:
            logger.info("Failed detaching partiton", partition=partition_name)
            raise e
