import datetime
import os

import structlog
from django.conf import settings
from django.db import connections

from etl import maintenance
from etl import materialize
from etl import redshift
from etl.materialize import MATERIALIZED_VIEWS
from utils import s3helpers
from utils.command_helpers import Z1Command

logger = structlog.get_logger(__name__)


class Command(Z1Command):
    def handle(self, *args, **options):
        # override settings required for this script
        settings.USE_S3 = True
        settings.S3_BUCKET_STATS = "z1-stats"

        job_id = self._get_latest_job_id()
        logger.info("Loading data from job", job=job_id)

        # dates are used for deleting old data
        date_from = datetime.date(2000, 1, 1)
        date_to = datetime.date.today()

        for db_name in settings.STATS_DB_WRITE_REPLICAS_POSTGRES:
            if settings.DATABASES[db_name]["NAME"] != "one-dev":
                raise Exception("This script should only run in dev environment")

            tables = connections[db_name].introspection.get_table_list(connections[db_name].cursor())
            existing_tables = set(table.name for table in tables)

            for mv_class in self._required_views():
                if mv_class.TABLE_NAME not in existing_tables:
                    self._create_table(db_name, mv_class)

                s3_path = os.path.join(redshift.MATERIALIZED_VIEWS_REPLICATION_S3_PREFIX, job_id, mv_class.TABLE_NAME)
                manifest = self._find_manifest(s3_path)
                redshift.update_table_from_s3_postgres(db_name, manifest, mv_class.TABLE_NAME, date_from, date_to)
                maintenance.vacuum(mv_class.TABLE_NAME, db_name=db_name)
                maintenance.analyze(mv_class.TABLE_NAME, db_name=db_name)

    def _find_manifest(self, s3_path):
        bucket = s3helpers.S3Helper(bucket_name=settings.S3_BUCKET_STATS)
        for f in bucket.list(s3_path):
            if f.key.endswith("manifest"):
                return f.key
        raise Exception("Manifest not found")

    def _get_latest_job_id(self):
        bucket = s3helpers.S3Helper(bucket_name=settings.S3_BUCKET_STATS)
        prefix = redshift.MATERIALIZED_VIEWS_REPLICATION_S3_PREFIX + "/"
        job_ids = self._list_folders(bucket, prefix)
        full_job_ids = [job_id for job_id in job_ids if job_id.count("_") == 1]

        if len(full_job_ids) == 0:
            raise Exception("No jobs found")

        # if latest job does not have all tables yet, use previous
        prefix += full_job_ids[-1] + "/"
        unloaded_tables = self._list_folders(bucket, prefix)
        for mv_class in self._required_views():
            if mv_class.TABLE_NAME not in unloaded_tables:
                if len(full_job_ids) < 2:
                    raise Exception("No completed jobs found")
                return full_job_ids[-2]

        return full_job_ids[-1]

    def _list_folders(self, bucket, prefix):
        prefixes = bucket.list(prefix, delimiter="/")
        return [pre.name.split("/")[-2] for pre in prefixes]

    def _required_views(self):
        for mv_class in MATERIALIZED_VIEWS:
            if mv_class.IS_TEMPORARY_TABLE:
                continue
            if mv_class in (materialize.MasterView, materialize.MasterPublishersView):
                # do not copy mv_master and mv_master_pubs into postgres, too large
                continue
            yield mv_class

    def _create_table(self, db_name, mv_class):
        if mv_class.IS_DERIVED_VIEW:
            sql = mv_class.prepare_create_table_postgres()
        else:
            migration_file = os.path.join(
                os.path.dirname(__file__), "../../../etl/migrations/postgres/", mv_class.TABLE_NAME + ".sql"
            )
            with open(migration_file) as f:
                sql = f.read()
        with connections[db_name].cursor() as cursor:
            cursor.execute(sql)
