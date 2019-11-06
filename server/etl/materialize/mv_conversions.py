import json
from functools import partial

from dateutil import rrule

from etl import helpers
from etl import redshift
from etl import s3
from redshiftapi import db
from utils import zlogging

from .materialize import Materialize
from .mv_master import MasterView

logger = zlogging.getLogger(__name__)


class MVConversions(Materialize):

    TABLE_NAME = "mv_conversions"

    def __init__(self, *args, **kwargs):
        super(MVConversions, self).__init__(*args, **kwargs)

        self.master_view = MasterView(self.job_id, self.date_from, self.date_to, self.account_id)

    def generate(self, **kwargs):

        self.master_view.prefetch()

        for date in rrule.rrule(rrule.DAILY, dtstart=self.date_from, until=self.date_to):
            date = date.date()

            with db.get_write_stats_transaction():
                with db.get_write_stats_cursor() as c:
                    logger.info("Deleting data from table", table=self.TABLE_NAME, date=date, job=self.job_id)
                    sql, params = redshift.prepare_daily_delete_query(self.TABLE_NAME, date, self.account_id)
                    c.execute(sql, params)

                    # generate csv in transaction as it needs data created in it
                    s3_path = s3.upload_csv(self.TABLE_NAME, date, self.job_id, partial(self.generate_rows, c, date))

                    logger.info("Copying CSV to table", table=self.TABLE_NAME, date=date, job=self.job_id)
                    sql, params = redshift.prepare_copy_query(s3_path, self.TABLE_NAME)
                    c.execute(sql, params)

    def generate_rows(self, cursor, date):
        for _, row, conversions_tuple in self.master_view.get_postclickstats(cursor, date):
            conversions = conversions_tuple[0]
            postclick_source = conversions_tuple[1]

            if conversions:
                conversions = json.loads(conversions)

                for slug, hits in conversions.items():
                    slug = helpers.get_conversion_prefix(postclick_source, slug)
                    yield tuple(list(row)[:8] + [slug, hits])
