from dateutil import rrule
from functools import partial
import logging
import os.path

from django.conf import settings

from etl import constants
from etl import s3
from etl import spark
from .materialize import Materialize

logger = logging.getLogger(__name__)


class MVHelpersCampaignFactors(Materialize):
    """
    Helper view that puts campaign factors into redshift. Its then used to construct the mv_master view.
    """

    TABLE_NAME = "mvh_campaign_factors"
    IS_TEMPORARY_TABLE = True
    SPARK_COLUMNS = [
        spark.Column("date", "string"),
        spark.Column("campaign_id", "int"),
        spark.Column("pct_actual_spend", "decimal", 22, 18),
        spark.Column("pct_license_fee", "decimal", 22, 18),
        spark.Column("pct_margin", "decimal", 22, 18),
    ]

    def generate(self, campaign_factors, **kwargs):
        self.check_date_range_continuation(campaign_factors)

        s3_path = os.path.join(constants.SPARK_S3_PREFIX, self.job_id, self.TABLE_NAME, "data.csv")
        s3.upload_csv(s3_path, partial(self.generate_rows, campaign_factors))

        self.spark_session.run_file(
            "load_csv_from_s3_to_table.py.tmpl",
            table=self.TABLE_NAME,
            s3_bucket=settings.S3_BUCKET_STATS,
            s3_path=s3_path,
            schema=spark.generate_schema(self.SPARK_COLUMNS),
        )
        self.spark_session.run_file("cache_table.py.tmpl", table=self.TABLE_NAME)

    def generate_rows(self, campaign_factors):
        for date, campaign_dict in campaign_factors.items():
            for campaign, factors in campaign_dict.items():
                yield (date, campaign.id, factors[0], factors[1], factors[2])

    def check_date_range_continuation(self, campaign_factors):
        # checks that all the dates withing the reprocessed date range have campaign factors set
        for dt in rrule.rrule(rrule.DAILY, dtstart=self.date_from, until=self.date_to):
            dt = dt.date()
            if dt not in campaign_factors:
                raise Exception(
                    "Campaign factors missing for the date %s within date range %s - %s, job %s",
                    dt,
                    self.date_from,
                    self.date_to,
                    self.job_id,
                )
