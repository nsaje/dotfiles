import backtosql
from etl import helpers
from etl import redshift
from redshiftapi import db
from utils import zlogging

from .materialize import Materialize

logger = zlogging.getLogger(__name__)


class MVAdGroupPlacement(Materialize):
    TABLE_NAME = "mv_adgroup_placement"

    def generate(self, **kwargs):
        with db.get_write_stats_transaction():
            with db.get_write_stats_cursor() as c:
                logger.info(
                    "Deleting data from table",
                    table=self.TABLE_NAME,
                    date_from=self.date_from,
                    date_to=self.date_to,
                    job=self.job_id,
                )
                sql, params = redshift.prepare_date_range_delete_query(
                    self.TABLE_NAME, self.date_from, self.date_to, self.account_id
                )
                c.execute(sql, params)

                # TODO: remove the 10 min statement timeout when the after midnight hangup is fixed
                c.execute("SET statement_timeout TO 600000;")

                logger.info(
                    "Running insert traffic data into table",
                    table=self.TABLE_NAME,
                    date_from=self.date_from,
                    date_to=self.date_to,
                    job=self.job_id,
                )
                sql, params = self.prepare_insert_traffic_data_query()
                c.execute(sql, params)

                c.execute("SET statement_timeout TO 0;")

    def prepare_insert_traffic_data_query(self):
        params = helpers.get_local_multiday_date_context(self.date_from, self.date_to)

        sql = backtosql.generate_sql(
            "etl_insert_mv_adgroup_placement.sql",
            {"date_ranges": params.pop("date_ranges"), "account_id": self.account_id},
        )

        params = self._add_account_id_param(params)
        params = self._add_ad_group_id_param(params)

        return sql, params
