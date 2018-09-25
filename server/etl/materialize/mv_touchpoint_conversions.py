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


class MVTouchpointConversions(Materialize):

    TABLE_NAME = "mv_touchpointconversions"
    SPARK_COLUMNS = [
        spark.Column("date", "string"),
        spark.Column("account_id", "int"),
        spark.Column("campaign_id", "int"),
        spark.Column("ad_group_id", "int"),
        spark.Column("content_ad_id", "int"),
        spark.Column("slug", "string"),
        spark.Column("conversion_id", "string"),
        spark.Column("conversion_timestamp", "string"),
        spark.Column("touchpoint_id", "string"),
        spark.Column("touchpoint_timestamp", "string"),
        spark.Column("zuid", "string", nullable=True),
        spark.Column("source_id", "int"),
        spark.Column("publisher", "string", nullable=True),
        spark.Column("conversion_lag", "int"),
        spark.Column("value_nano", "long", nullable=True),
        spark.Column("label", "string", nullable=True),
        spark.Column("device_type", "int", nullable=True),
        spark.Column("device_os", "string", nullable=True),
        spark.Column("device_os_version", "string", nullable=True),
        spark.Column("placement_medium", "string", nullable=True),
        spark.Column("country", "string", nullable=True),
        spark.Column("state", "string", nullable=True),
        spark.Column("dma", "int", nullable=True),
    ]

    def generate(self, **kwargs):
        INPUT_TABLE = "conversions"

        redshift.unload_table(
            self.job_id,
            INPUT_TABLE,
            self.date_from,
            self.date_to,
            prefix=constants.SPARK_S3_PREFIX,
            account_id=self.account_id,
        )

        self.spark_session.run_file(
            "load_csv_from_s3_to_table.py.tmpl",
            table=INPUT_TABLE,
            s3_bucket=settings.S3_BUCKET_STATS,
            s3_path=os.path.join(constants.SPARK_S3_PREFIX, self.job_id, INPUT_TABLE, "*.gz"),
            schema=spark.generate_schema(self.SPARK_COLUMNS),
        )

        sql = self.prepare_spark_query()
        self.spark_session.run_file("sql_to_table.py.tmpl", sql=sql, table=self.TABLE_NAME)

        self.spark_session.run_file("cache_table.py.tmpl", table=self.TABLE_NAME)

        s3_path = os.path.join(constants.SPARK_S3_PREFIX, self.job_id, self.TABLE_NAME) + "/"
        self.spark_session.run_file(
            "export_table_to_json_s3.py.tmpl",
            table=self.TABLE_NAME,
            s3_bucket=settings.S3_BUCKET_STATS,
            s3_path=s3_path,
        )
        redshift.update_table_from_s3_json(s3_path, self.TABLE_NAME, self.date_from, self.date_to, self.account_id)

    def prepare_spark_query(self):
        outbrain = helpers.get_outbrain()
        yahoo = helpers.get_yahoo()
        params = {
            "date_from": self.date_from.isoformat(),
            "date_to": self.date_to.isoformat(),
            "account_id": self.account_id,
            "outbrain_id": outbrain.id,
            "yahoo_id": yahoo.id,
        }
        self._add_ad_group_id_param(params)

        sql = backtosql.generate_sql("etl_spark_mv_touchpointconversions.sql", params)

        return sql
