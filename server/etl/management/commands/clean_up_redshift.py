import datetime

from django.conf import settings

import utils.dates_helper
from etl import maintenance
from etl import redshift
from etl import refresh
from redshiftapi import db
from utils import metrics_compat
from utils import zlogging
from utils.command_helpers import Z1Command

logger = zlogging.getLogger(__name__)

STATS_DB_HOT_CLUSTER = settings.STATS_DB_HOT_CLUSTER
STATS_DB_HOT_CLUSTER_MAX_DAYS = settings.STATS_DB_HOT_CLUSTER_MAX_DAYS
RAW_TABLES_CONFIG = [
    {"table_name": "supply_stats", "keep_days": 31},
    {"table_name": "stats", "keep_days": 93},
    {"table_name": "stats_placement", "keep_days": 93},
]


class Command(Z1Command):
    @metrics_compat.timer("etl.clean_up_redshift")
    def handle(self, *args, **options):
        for table_name in refresh.get_all_views_table_names():
            self._clean_up_table(table_name, STATS_DB_HOT_CLUSTER_MAX_DAYS)
        for config in RAW_TABLES_CONFIG:
            table_name = config["table_name"]
            keep_days = config["keep_days"]
            self._clean_up_table(table_name, keep_days)

    def _clean_up_table(self, table_name, keep_days):
        self._delete_old_data(table_name, keep_days)
        try:
            maintenance.vacuum(table_name, delete_only=True, db_name=STATS_DB_HOT_CLUSTER)
            maintenance.analyze(table_name, db_name=STATS_DB_HOT_CLUSTER)
        except Exception:
            logger.exception("Vacuum after cleanup failed, skipping", table=table_name)

    @staticmethod
    def _delete_old_data(table, keep_days):
        date_from = datetime.date(1970, 1, 1)
        date_to = utils.dates_helper.days_before(utils.dates_helper.local_today(), keep_days)
        with db.get_write_stats_cursor() as c:
            logger.info("Deleting old data from table", table=table)
            sql, params = redshift.prepare_date_range_delete_query(table, date_from, date_to, None)
            c.execute(sql, params)
