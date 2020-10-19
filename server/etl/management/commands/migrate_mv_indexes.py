from django.conf import settings

from etl.materialize import MATERIALIZED_VIEWS
from redshiftapi import db
from utils import zlogging
from utils.command_helpers import Z1Command

logger = zlogging.getLogger(__name__)

STATS_DB_POSTGRES = settings.STATS_DB_POSTGRES

CREATE_INDEX_SQL = "CREATE INDEX IF NOT EXISTS {}_idx ON {} ({});"
DROP_INDEX_SQL = "DROP INDEX IF EXISTS {}_main_idx;"


class Command(Z1Command):
    help = "Migrate MV derived views table indexes"

    def add_arguments(self, parser):
        parser.add_argument("--drop-old-indexes", action="store_true", help="Drop old indexes from the MV tables")

    def handle(self, *args, **options):
        drop_old_indexes = options.get("drop_old_indexes")

        for mv in MATERIALIZED_VIEWS:
            if not mv.IS_DERIVED_VIEW:
                continue

            if drop_old_indexes:
                logger.info("Dropping old index on table", table=mv.TABLE_NAME)
                sql = DROP_INDEX_SQL.format(mv.TABLE_NAME)
            else:
                logger.info("Creating index on table", index=mv.INDEX, table=mv.TABLE_NAME)
                sql = CREATE_INDEX_SQL.format(mv.TABLE_NAME, mv.TABLE_NAME, ",".join(mv.INDEX))

            for pg_db_name in STATS_DB_POSTGRES:
                with db.get_write_stats_cursor(pg_db_name) as cursor:
                    cursor.execute(sql)
