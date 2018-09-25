import backtosql
import logging
import os.path

from django.conf import settings

from etl import constants
from etl import helpers
from etl import redshift
from etl import spark
from .materialize import Materialize

logger = logging.getLogger(__name__)


class MasterPublishersView(Materialize):

    TABLE_NAME = "mv_master_pubs"
    OUTBRAIN_OUTPUT_TABLE_NAME = "mv_master_pubs_outbrain"
    OUTBRAIN_TABLE_NAME = "outbrainpublisherstats"
    OUTBRAIN_SPARK_COLUMNS = [
        spark.Column("date", "string"),
        spark.Column("ad_group_id", "int"),
        spark.Column("publisher_id", "string", nullable=True),
        spark.Column("publisher_name", "string", nullable=True),
        spark.Column("clicks", "int", nullable=True),
        spark.Column("impressions", "int", nullable=True),
        spark.Column("spend", "long", nullable=True),
    ]
    POSTCLICK_TABLE_NAME = "postclickstats"
    POSTCLICK_SPARK_COLUMNS = [
        spark.Column("date", "string"),
        spark.Column("type", "string"),
        spark.Column("content_ad_id", "int"),
        spark.Column("ad_group_id", "int"),
        spark.Column("source", "string"),
        spark.Column("publisher", "string", nullable=True),
        spark.Column("visits", "int", nullable=True),
        spark.Column("new_visits", "int", nullable=True),
        spark.Column("bounced_visits", "int", nullable=True),
        spark.Column("pageviews", "int", nullable=True),
        spark.Column("total_time_on_site", "int", nullable=True),
        spark.Column("conversions", "string", nullable=True),
        spark.Column("users", "int", nullable=True),
    ]

    def __init__(self, *args, **kwargs):
        self.outbrain = helpers.get_outbrain()
        self.yahoo = helpers.get_yahoo()
        super(MasterPublishersView, self).__init__(*args, **kwargs)

    def generate(self, **kwargs):
        redshift.unload_table(
            self.job_id, self.OUTBRAIN_TABLE_NAME, self.date_from, self.date_to, prefix=constants.SPARK_S3_PREFIX
        )
        self.spark_session.run_file(
            "load_csv_from_s3_to_table.py.tmpl",
            table=self.OUTBRAIN_TABLE_NAME,
            s3_bucket=settings.S3_BUCKET_STATS,
            s3_path=os.path.join(constants.SPARK_S3_PREFIX, self.job_id, self.OUTBRAIN_TABLE_NAME, "*.gz"),
            schema=spark.generate_schema(self.OUTBRAIN_SPARK_COLUMNS),
        )

        redshift.unload_table(
            self.job_id, self.POSTCLICK_TABLE_NAME, self.date_from, self.date_to, prefix=constants.SPARK_S3_PREFIX
        )
        self.spark_session.run_file(
            "load_csv_from_s3_to_table.py.tmpl",
            table=self.POSTCLICK_TABLE_NAME,
            s3_bucket=settings.S3_BUCKET_STATS,
            s3_path=os.path.join(constants.SPARK_S3_PREFIX, self.job_id, self.POSTCLICK_TABLE_NAME, "*.gz"),
            schema=spark.generate_schema(self.POSTCLICK_SPARK_COLUMNS),
        )

        # outbrain
        sql = self.prepare_outbrain_spark_query()
        self.spark_session.run_file("sql_to_table.py.tmpl", sql=sql, table=self.OUTBRAIN_OUTPUT_TABLE_NAME)

        # from master
        sql = self.prepare_mv_master_spark_query()
        self.spark_session.run_file("sql_to_table.py.tmpl", sql=sql, table=self.TABLE_NAME)

        # union
        self.spark_session.run_file(
            "union_tables.py.tmpl",
            table=self.TABLE_NAME,
            source_table_1=self.TABLE_NAME,
            source_table_2=self.OUTBRAIN_OUTPUT_TABLE_NAME,
        )

        # cache
        self.spark_session.run_file("cache_table.py.tmpl", table=self.TABLE_NAME)

        # load to redshift
        s3_path = os.path.join(constants.SPARK_S3_PREFIX, self.job_id, self.TABLE_NAME) + "/"
        self.spark_session.run_file(
            "export_table_to_json_s3.py.tmpl",
            table=self.TABLE_NAME,
            s3_bucket=settings.S3_BUCKET_STATS,
            s3_path=s3_path,
        )
        redshift.update_table_from_s3_json(s3_path, self.TABLE_NAME, self.date_from, self.date_to, self.account_id)

    def prepare_mv_master_spark_query(self):
        sql = backtosql.generate_sql(
            "etl_spark_mv_pubs_master.sql",
            {
                "account_id": self.account_id,
                "date_from": self.date_from.isoformat(),
                "date_to": self.date_to.isoformat(),
            },
        )

        return sql

    def prepare_outbrain_spark_query(self):
        params = {
            "source_id": self.outbrain.id,
            "account_id": self.account_id,
            "date_from": self.date_from.isoformat(),
            "date_to": self.date_to.isoformat(),
        }
        params = self._add_ad_group_id_param(params)
        sql = backtosql.generate_sql("etl_spark_mv_pubs_outbrain.sql", params)

        return sql
