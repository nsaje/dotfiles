from functools import partial

from dateutil import rrule

import backtosql
from etl import redshift
from etl import s3
from redshiftapi import db
from utils import zlogging

from .materialize import Materialize

logger = zlogging.getLogger(__name__)


class MVHelpersCampaignFactors(Materialize):
    """
    Helper view that puts campaign factors into redshift. Its then used to construct the mv_master view.
    """

    TABLE_NAME = "mvh_campaign_factors"
    IS_TEMPORARY_TABLE = True

    def generate(self, campaign_factors, **kwargs):
        self.check_date_range_continuation(campaign_factors)

        s3_path = s3.upload_csv(
            self.TABLE_NAME, self.date_to, self.job_id, partial(self.generate_rows, campaign_factors)
        )

        with db.get_write_stats_transaction():
            with db.get_write_stats_cursor() as c:
                sql = backtosql.generate_sql("etl_create_temp_table_mvh_campaign_factors.sql", None)
                c.execute(sql)

                logger.info("Copying CSV to table", table=self.TABLE_NAME, job=self.job_id)
                sql, params = redshift.prepare_copy_query(s3_path, self.TABLE_NAME)
                c.execute(sql, params)
                logger.info("Copied CSV to table", table=self.TABLE_NAME, job=self.job_id)

    def generate_rows(self, campaign_factors):
        for date, campaign_dict in campaign_factors.items():
            for campaign, factors in campaign_dict.items():
                yield (date, campaign.id, factors[0], factors[1], factors[2], factors[3])

    def check_date_range_continuation(self, campaign_factors):
        # checks that all the dates withing the reprocessed date range have campaign factors set
        for dt in rrule.rrule(rrule.DAILY, dtstart=self.date_from, until=self.date_to):
            dt = dt.date()
            if dt not in campaign_factors:
                raise Exception(
                    "Campaign factors missing",
                    date=dt,
                    date_from=self.date_from,
                    date_to=self.date_to,
                    job_id=self.job_id,
                )
