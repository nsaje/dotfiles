import structlog
from dateutil import rrule

import backtosql
import core.features.multicurrency
import dash.models
from etl import redshift
from etl import s3
from redshiftapi import db

from .materialize import Materialize

logger = structlog.get_logger(__name__)


class MVHelpersCurrencyExchangeRates(Materialize):

    TABLE_NAME = "mvh_currency_exchange_rates"
    IS_TEMPORARY_TABLE = True

    def generate(self, **kwargs):
        s3_path = s3.upload_csv(self.TABLE_NAME, self.date_to, self.job_id, self.generate_rows)

        with db.get_write_stats_transaction():
            with db.get_write_stats_cursor() as c:
                sql = backtosql.generate_sql("etl_create_temp_table_mvh_currency_exchange_rates.sql", None)
                c.execute(sql)

                logger.info("Copying CSV to table", table=self.TABLE_NAME, job=self.job_id)
                sql, params = redshift.prepare_copy_query(s3_path, self.TABLE_NAME)
                c.execute(sql, params)
                logger.info("Copied CSV to table", table=self.TABLE_NAME, job=self.job_id)

    def generate_rows(self):
        accounts = dash.models.Account.objects.filter(currency__isnull=False).order_by("pk")

        for account in accounts:
            for date in rrule.rrule(rrule.DAILY, dtstart=self.date_from, until=self.date_to):
                yield (date.date(), account.id, core.features.multicurrency.get_exchange_rate(date, account.currency))
