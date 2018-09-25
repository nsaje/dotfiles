import backtosql
import logging
import os.path

from django.conf import settings

import dash.models

from etl import constants
from etl import helpers
from etl import redshift
from etl import spark
from .materialize import Materialize

logger = logging.getLogger(__name__)


class MVHelpersNormalizedStats(Materialize):
    """
    Writes a temporary table that has data from stats transformed into the correct format for mv_master construction.
    It does conversion from age, gender etc. strings to constatnts, calculates nano, calculates effective cost
    and license fee based on mvh_campaign_factors.
    """

    TABLE_NAME = "mvh_clean_stats"
    IS_TEMPORARY_TABLE = True
    SPARK_COLUMNS = [
        spark.Column("date", "string"),
        spark.Column("hour", "int", nullable=True),
        spark.Column("media_source_type", "string"),
        spark.Column("media_source", "string"),
        spark.Column("content_ad_id", "int"),
        spark.Column("ad_group_id", "int"),
        spark.Column("device_type", "int", nullable=True),
        spark.Column("device_os", "string", nullable=True),
        spark.Column("device_os_version", "string", nullable=True),
        spark.Column("country", "string", nullable=True),
        spark.Column("state", "string", nullable=True),
        spark.Column("dma", "int", nullable=True),
        spark.Column("city_id", "int", nullable=True),
        spark.Column("placement_type", "int", nullable=True),
        spark.Column("video_playback_method", "int", nullable=True),
        spark.Column("age", "string", nullable=True),
        spark.Column("gender", "string", nullable=True),
        spark.Column("placement_medium", "string", nullable=True),
        spark.Column("publisher", "string", nullable=True),
        spark.Column("impressions", "int", nullable=True),
        spark.Column("clicks", "int", nullable=True),
        spark.Column("spend", "long", nullable=True),
        spark.Column("data_spend", "long", nullable=True),
        spark.Column("video_start", "int", nullable=True),
        spark.Column("video_first_quartile", "int", nullable=True),
        spark.Column("video_midpoint", "int", nullable=True),
        spark.Column("video_third_quartile", "int", nullable=True),
        spark.Column("video_complete", "int", nullable=True),
        spark.Column("video_progress_3s", "int", nullable=True),
        spark.Column("campaign_id", "int", nullable=True),
        spark.Column("account_id", "int", nullable=True),
        spark.Column("agency_id", "int", nullable=True),
        spark.Column("original_spend", "long", nullable=True),
    ]

    def generate(self, **kwargs):
        INPUT_TABLE = "stats"

        redshift.unload_table_tz(
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

    def prepare_spark_query(self):
        params = helpers.get_local_multiday_date_context(self.date_from, self.date_to)
        params["account_id"] = self.account_id
        params["yahoo_slug"] = helpers.get_yahoo().bidder_slug
        params["outbrain_slug"] = helpers.get_outbrain().bidder_slug
        params["valid_placement_mediums"] = dash.constants.PlacementMedium.get_all()
        self._add_ad_group_id_param(params)

        sql = backtosql.generate_sql("etl_spark_mvh_clean_stats.sql", params)

        return sql
