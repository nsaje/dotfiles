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
LOCK_TIMEOUT = "2s"


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
        self._set_lock_timeout(cursor, LOCK_TIMEOUT)

        for i in range(1, PARTITION_CHECK_DAYS + 1):
            date_from = today + datetime.timedelta(i)
            date_to = today + datetime.timedelta(i + 1)
            self._create_partition(cursor, date_from, date_to)

    def _create_partition(self, cursor, date_from, date_to):
        partition_name = "dash_historystacktrace_{date_postfix}".format(date_postfix=date_from.strftime("%Y%m%d"))
        sql = """
            CREATE TABLE IF NOT EXISTS
                {partition_name}
            PARTITION OF
                dash_historystacktrace
            FOR VALUES FROM ('{date_from}') TO ('{date_to}');
        """
        self._execute_sql_with_retry(
            cursor,
            sql.format(partition_name=partition_name, date_from=date_from, date_to=date_to),
            "Failed creating partiton",
            partition=partition_name,
        )

    def _delete_old_partitions(self, today):
        cursor = connection.cursor()
        self._set_lock_timeout(cursor, LOCK_TIMEOUT)

        for i in range(1, PARTITION_CHECK_DAYS + 1):
            date = today - datetime.timedelta(HISTORY_DATA_KEEP_DAYS + i)
            partition_name = "dash_historystacktrace_{date_postfix}".format(date_postfix=date.strftime("%Y%m%d"))
            self.delete_partition(cursor, partition_name)

    def delete_partition(self, cursor, partition_name):
        self._detach_partition(cursor, partition_name)
        self._delete_partition(cursor, partition_name)

    def _detach_partition(self, cursor, partition_name):
        sql = f"ALTER TABLE dash_historystacktrace DETACH PARTITION {partition_name};"
        self._execute_sql_with_retry(cursor, sql, "Failed detaching partiton", partition=partition_name)

    def _delete_partition(self, cursor, partition_name):
        sql = f"DROP TABLE IF EXISTS {partition_name};"
        self._execute_sql_with_retry(cursor, sql, "Failed deleting partiton", partition=partition_name)

    @retrying.retry(
        retry_on_exception=lambda e: isinstance(e, OperationalError)
        and "canceling statement due to lock timeout" in str(e)
        or "deadlock detected" in str(e),
        stop_max_attempt_number=50,
        wait_exponential_multiplier=1000,
        wait_exponential_max=10000,
    )
    def _execute_sql_with_retry(self, cursor, sql, log_message, **log_kwargs):
        try:
            cursor.execute(sql)
        except ProgrammingError:
            # something wrong - e.g. partition does not exist
            pass
        except OperationalError as e:
            logger.info(log_message, **log_kwargs)
            raise e

    def _set_lock_timeout(self, cursor, timeout):
        cursor.execute(f"SET lock_timeout TO '{timeout}';")
