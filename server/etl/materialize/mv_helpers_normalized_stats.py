import structlog

import backtosql
import dash.models
from etl import helpers
from redshiftapi import db

from .materialize import Materialize

logger = structlog.get_logger(__name__)


class MVHelpersNormalizedStats(Materialize):
    """
    Writes a temporary table that has data from stats transformed into the correct format for mv_master construction.
    It does conversion from age, gender etc. strings to constatnts, calculates nano, calculates effective cost
    and license fee based on mvh_campaign_factors.
    """

    TABLE_NAME = "mvh_clean_stats"
    IS_TEMPORARY_TABLE = True

    def generate(self, **kwargs):
        with db.get_write_stats_transaction():
            with db.get_write_stats_cursor() as c:
                sql = backtosql.generate_sql("etl_create_temp_table_mvh_clean_stats.sql", None)
                c.execute(sql)

                logger.info("Running insert into table", table=self.TABLE_NAME, job=self.job_id)
                sql, params = self.prepare_insert_query()

                c.execute(sql, params)
                logger.info("Done insert into table", table=self.TABLE_NAME, job=self.job_id)

    def prepare_insert_query(self):
        yahoo = helpers.get_yahoo()
        params = helpers.get_local_multiday_date_context(self.date_from, self.date_to)

        sql = backtosql.generate_sql(
            "etl_insert_mvh_clean_stats.sql",
            {
                "date_ranges": params.pop("date_ranges"),
                "account_id": self.account_id,
                "yahoo_slug": yahoo.bidder_slug,
                "valid_placement_mediums": dash.constants.PlacementMedium.get_all(),
            },
        )

        return sql, self._add_ad_group_id_param(params)
