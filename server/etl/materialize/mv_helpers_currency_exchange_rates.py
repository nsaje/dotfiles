from dateutil import rrule
import logging
import os.path

from django.conf import settings

import core.multicurrency
import dash.models

from etl import constants
from etl import s3
from etl import spark
from .materialize import Materialize

logger = logging.getLogger(__name__)


class MVHelpersCurrencyExchangeRates(Materialize):

    TABLE_NAME = "mvh_currency_exchange_rates"
    IS_TEMPORARY_TABLE = True
    SPARK_COLUMNS = [
        spark.Column("date", "string"),
        spark.Column("account_id", "int"),
        spark.Column("exchange_rate", "decimal", 10, 4),
    ]

    def generate(self, **kwargs):
        s3_path = os.path.join(constants.SPARK_S3_PREFIX, self.job_id, self.TABLE_NAME, "data.csv")
        s3.upload_csv(s3_path, self.generate_rows)

        self.spark_session.run_file(
            "load_csv_from_s3_to_table.py.tmpl",
            table=self.TABLE_NAME,
            s3_bucket=settings.S3_BUCKET_STATS,
            s3_path=s3_path,
            schema=spark.generate_schema(self.SPARK_COLUMNS),
        )
        self.spark_session.run_file("cache_table.py.tmpl", table=self.TABLE_NAME)

    def generate_rows(self):
        accounts = dash.models.Account.objects.filter(currency__isnull=False)

        for account in accounts:
            for date in rrule.rrule(rrule.DAILY, dtstart=self.date_from, until=self.date_to):
                yield (date.date(), account.id, core.multicurrency.get_exchange_rate(date, account.currency))
