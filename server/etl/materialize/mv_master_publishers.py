import backtosql
import structlog
from etl import helpers
from etl import redshift
from redshiftapi import db

from .materialize import Materialize

logger = structlog.get_logger(__name__)


class MasterPublishersView(Materialize):

    TABLE_NAME = "mv_master_pubs"

    def __init__(self, *args, **kwargs):
        self.outbrain = helpers.get_outbrain()
        self.yahoo = helpers.get_yahoo()
        super(MasterPublishersView, self).__init__(*args, **kwargs)

    def generate(self, **kwargs):
        with db.get_write_stats_transaction():
            with db.get_write_stats_cursor() as c:
                logger.info(
                    'Deleting data from table "%s" for date range %s - %s, job %s',
                    self.TABLE_NAME,
                    self.date_from,
                    self.date_to,
                    self.job_id,
                )
                sql, params = redshift.prepare_date_range_delete_query(
                    self.TABLE_NAME, self.date_from, self.date_to, self.account_id
                )
                c.execute(sql, params)

                logger.info(
                    'Inserting non-Outbrain data into table "%s" for date range %s - %s, job %s',
                    self.TABLE_NAME,
                    self.date_from,
                    self.date_to,
                    self.job_id,
                )
                sql, params = self.prepare_select_insert_mv_master_pubs()
                c.execute(sql, params)

                logger.info(
                    'Inserting Outbrain data into table "%s" for date range %s - %s, job %s',
                    self.TABLE_NAME,
                    self.date_from,
                    self.date_to,
                    self.job_id,
                )
                sql, params = self.prepare_select_insert_outbrain_to_mv_master_pubs()
                c.execute(sql, params)

    def prepare_select_insert_mv_master_pubs(self):
        sql = backtosql.generate_sql("etl_select_insert_mv_pubs_master.sql", {"account_id": self.account_id})

        return sql, self._add_account_id_param({"date_from": self.date_from, "date_to": self.date_to})

    def prepare_select_insert_outbrain_to_mv_master_pubs(self):
        sql = backtosql.generate_sql(
            "etl_select_insert_outbrain_to_mv_pubs_master.sql",
            {"source_id": self.outbrain.id, "account_id": self.account_id},
        )

        return sql, self._add_ad_group_id_param({"date_from": self.date_from, "date_to": self.date_to})
