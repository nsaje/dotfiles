import logging
import os.path

from django.conf import settings

import backtosql
import dash.models
from etl import constants
from etl import helpers
from etl import redshift
from redshiftapi import db

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

    def generate(self, **kwargs):
        INPUT_TABLE = "stats"

        logger.info("Running unload from table stats for %s, job %s", self.TABLE_NAME, self.job_id)
        redshift.unload_table_tz(
            self.job_id,
            INPUT_TABLE,
            self.date_from,
            self.date_to,
            prefix=constants.SPARK_S3_PREFIX,
            account_id=self.account_id,
        )
        logger.info("Done unload from table stats for %s, job %s", self.TABLE_NAME, self.job_id)

        logger.info("Running spark for %s, job %s", self.TABLE_NAME, self.job_id)
        sql = self.prepare_spark_query()
        self.spark_session.run_file(
            "mvh_clean_stats.py",
            sql=sql,
            bucket=settings.S3_BUCKET_STATS,
            prefix=constants.SPARK_S3_PREFIX,
            job_id=self.job_id,
            input_table=INPUT_TABLE,
            output_table=self.TABLE_NAME,
        )
        logger.info("Done spark for %s, job %s", self.TABLE_NAME, self.job_id)

        with db.get_write_stats_transaction():
            with db.get_write_stats_cursor() as c:
                sql = backtosql.generate_sql("etl_create_temp_table_mvh_clean_stats.sql", None)
                c.execute(sql)

                logger.info('Running copy into table "%s", job %s', self.TABLE_NAME, self.job_id)
                sql, params = redshift.prepare_copy_query(
                    os.path.join(constants.SPARK_S3_PREFIX, self.job_id, self.TABLE_NAME),
                    self.TABLE_NAME,
                    format="json",
                    gzip=True,
                )

                c.execute(sql, params)
                logger.info('Done copy into table "%s", job %s', self.TABLE_NAME, self.job_id)

    def prepare_spark_query(self):
        params = helpers.get_local_multiday_date_context(self.date_from, self.date_to)
        params["account_id"] = self.account_id
        params["yahoo_slug"] = helpers.get_yahoo().bidder_slug
        params["outbrain_slug"] = helpers.get_outbrain().bidder_slug
        params["valid_placement_mediums"] = dash.constants.PlacementMedium.get_all()
        self._add_ad_group_id_param(params)

        sql = backtosql.generate_sql("etl_spark_mvh_clean_stats.sql", params)

        return sql
