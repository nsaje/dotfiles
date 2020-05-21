from django.conf import settings
from django.core.management.base import BaseCommand

from etl import redshift
from etl import refresh
from etl.materialize import MATERIALIZED_VIEWS
from redshiftapi import db
from utils import dates_helper
from utils import zlogging

logger = zlogging.getLogger(__name__)

STATS_DB_COLD_CLUSTER = settings.STATS_DB_COLD_CLUSTERS[0]
STATS_DB_HOT_CLUSTER = settings.STATS_DB_HOT_CLUSTER
STATS_DB_POSTGRES = settings.STATS_DB_POSTGRES
STATS_DB_HOT_CLUSTER_MAX_DAYS = settings.STATS_DB_HOT_CLUSTER_MAX_DAYS
STATS_DB_POSTGRES_MAX_DAYS = settings.STATS_DB_POSTGRES_MAX_DAYS


class Command(BaseCommand):
    help = "Create a new derived table in the cold cluster and replicate it to the hot one and the postgres replicas."

    def add_arguments(self, parser):
        parser.add_argument("new_derived_view_name", type=str)

    def handle(self, *args, **options):
        create_derived_view(options["new_derived_view_name"])


def create_derived_view(new_derived_view_name):
    job_id = refresh.generate_job_id(None)
    date_to = dates_helper.local_today()
    mv_class = _get_mv_class(new_derived_view_name)

    # Update cold cluster
    _create_mv_redshift(job_id, mv_class, STATS_DB_COLD_CLUSTER, backfill_data=True)

    # Update hot cluster
    date_from = dates_helper.days_before(date_to, STATS_DB_HOT_CLUSTER_MAX_DAYS)
    _create_mv_redshift(job_id, mv_class, STATS_DB_HOT_CLUSTER)
    _update_mv_redshift(job_id, mv_class, date_from, date_to, STATS_DB_COLD_CLUSTER, STATS_DB_HOT_CLUSTER)

    # Update postgres replicas
    date_from = dates_helper.days_before(date_to, STATS_DB_POSTGRES_MAX_DAYS)
    s3_path = None
    for pg_db_name in STATS_DB_POSTGRES:
        _create_mv_postgres(job_id, mv_class, pg_db_name)
        s3_path = _update_mv_postgres(
            job_id, mv_class, date_from, date_to, STATS_DB_COLD_CLUSTER, pg_db_name, s3_path=s3_path
        )


def _get_mv_class(new_derived_view_name):
    for mv in MATERIALIZED_VIEWS:
        if mv.TABLE_NAME == new_derived_view_name and mv.IS_DERIVED_VIEW and not mv.IS_TEMPORARY_TABLE:
            return mv

    raise Exception("A new derived view should be configured in MATERIALIZED_VIEWS list")


def _create_mv_redshift(job_id, mv_class, db_name, backfill_data=False):
    with db.get_write_stats_cursor(db_name) as cursor:
        _log_create(job_id, mv_class, db_name)
        sql = mv_class.prepare_create_table()
        cursor.execute(sql)

        if not backfill_data:
            return

        cursor.execute("SELECT count(1) FROM {}".format(mv_class.TABLE_NAME))
        count = cursor.fetchone()[0]

        if not count:
            logger.info(
                "Filling empty materialized view",
                table=mv_class.TABLE_NAME,
                breakdown=mv_class.BREAKDOWN,
                job_id=job_id,
                database=db_name,
            )
            sql, params = mv_class(job_id, date_from=None, date_to=None, account_id=None).prepare_insert_query(
                None, None
            )
            cursor.execute(sql, params)


def _create_mv_postgres(job_id, mv_class, db_name):
    with db.get_write_stats_cursor(db_name) as cursor:
        _log_create(job_id, mv_class, db_name)
        sql = mv_class.prepare_create_table_postgres()
        cursor.execute(sql)


def _update_mv_redshift(job_id, mv_class, date_from, date_to, source_db_name, dest_db_name, s3_path=None):
    if not s3_path:
        s3_path = redshift.unload_table(job_id, mv_class.TABLE_NAME, date_from, date_to, db_name=source_db_name)
    _log_update(job_id, mv_class, dest_db_name)
    redshift.update_table_from_s3(dest_db_name, s3_path, mv_class.TABLE_NAME, date_from, date_to)
    return s3_path


def _update_mv_postgres(job_id, mv_class, date_from, date_to, source_db_name, dest_db_name, s3_path=None):
    if not s3_path:
        s3_path = redshift.unload_table(job_id, mv_class.TABLE_NAME, date_from, date_to, db_name=source_db_name)
    _log_update(job_id, mv_class, dest_db_name)
    redshift.update_table_from_s3_postgres(dest_db_name, s3_path, mv_class.TABLE_NAME, date_from, date_to)
    return s3_path


def _log_create(job_id, mv_class, db_name):
    logger.info(
        "Creating materialized view table if it doesn't exist",
        table=mv_class.TABLE_NAME,
        breakdown=mv_class.BREAKDOWN,
        job_id=job_id,
        database=db_name,
    )


def _log_update(job_id, mv_class, db_name):
    logger.info(
        "Copying CSV to table", table=mv_class.TABLE_NAME, breakdown=mv_class.BREAKDOWN, job_id=job_id, database=db_name
    )
