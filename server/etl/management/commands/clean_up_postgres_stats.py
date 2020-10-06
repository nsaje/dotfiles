from django.conf import settings

from etl import helpers
from etl import maintenance
from etl import refresh
from redshiftapi import db
from utils import metrics_compat
from utils import zlogging
from utils.command_helpers import Z1Command

logger = zlogging.getLogger(__name__)


POSTGRES_KEEP_DAYS = 64
SKIP_TABLES = ["mv_master", "mv_adgroup_placement"]  # not on postgres


class Command(Z1Command):
    @metrics_compat.timer("etl.clean_up_postgres_stats")
    def handle(self, *args, **options):
        for db_name in settings.STATS_DB_POSTGRES:
            for table_name in refresh.get_all_views_table_names():
                if table_name in SKIP_TABLES:
                    continue
                self._drop_old_timescale_hypertable_chunks(table_name, db_name)
                maintenance.analyze(table_name, db_name=db_name)

    @staticmethod
    def _drop_old_timescale_hypertable_chunks(table_name: str, db_name: str):
        with db.get_write_stats_cursor(db_name) as c:
            logger.info("Dropping old timescale hypertable chunks from table", table_name=table_name)
            sql = helpers.prepare_drop_timescale_hypertable_chunks(table_name, POSTGRES_KEEP_DAYS)
            c.execute(sql)
