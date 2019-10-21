import structlog

import backtosql
from etl import helpers
from etl import redshift
from redshiftapi import db

from .materialize import Materialize

logger = structlog.get_logger(__name__)


class MVTouchpointConversions(Materialize):

    TABLE_NAME = "mv_touchpointconversions"

    def generate(self, **kwargs):
        with db.get_write_stats_transaction():
            with db.get_write_stats_cursor() as c:
                logger.info(
                    "Deleting data from table",
                    table=self.TABLE_NAME,
                    date_from=self.date_from,
                    date_to=self.date_to,
                    job_id=self.job_id,
                )
                sql, params = redshift.prepare_date_range_delete_query(
                    self.TABLE_NAME, self.date_from, self.date_to, self.account_id
                )
                c.execute(sql, params)

                logger.info(
                    "Inserting data into table",
                    table=self.TABLE_NAME,
                    date_from=self.date_from,
                    date_to=self.date_to,
                    job_id=self.job_id,
                )
                sql, params = self.prepare_insert_query()
                c.execute(sql, params)

    def prepare_insert_query(self):
        outbrain = helpers.get_outbrain()
        yahoo = helpers.get_yahoo()
        sql = backtosql.generate_sql(
            "etl_insert_mv_touchpointconversions.sql",
            {"account_id": self.account_id, "outbrain_id": outbrain.id, "yahoo_id": yahoo.id},
        )

        return sql, self._add_account_id_param({"date_from": self.date_from, "date_to": self.date_to})
