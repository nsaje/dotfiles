from dateutil import rrule
from functools import partial
import json
import logging
import os.path

from django.conf import settings

from redshiftapi import db

from etl import constants
from etl import helpers
from etl import spark
from etl import s3
from etl import redshift
from .mv_master_spark import MasterSpark
from .materialize import Materialize

logger = logging.getLogger(__name__)


class MVConversions(Materialize):

    TABLE_NAME = "mv_conversions"
    SPARK_COLUMNS = [
        spark.Column("date", "string"),
        spark.Column("source_id", "int"),
        spark.Column("account_id", "int"),
        spark.Column("campaign_id", "int"),
        spark.Column("ad_group_id", "int"),
        spark.Column("content_ad_id", "int"),
        spark.Column("publisher", "string", nullable=True),
        spark.Column("publisher_source_id", "string", nullable=True),
        spark.Column("slug", "string", nullable=True),
        spark.Column("conversion_count", "int", nullable=True),
    ]

    def __init__(self, *args, **kwargs):
        super(MVConversions, self).__init__(*args, **kwargs)

        self.master_view = MasterSpark(self.job_id, self.date_from, self.date_to, self.account_id)

    def generate(self, **kwargs):
        self.master_view.prefetch()

        for date in rrule.rrule(rrule.DAILY, dtstart=self.date_from, until=self.date_to):
            date = date.date()

            with db.get_write_stats_transaction():
                with db.get_write_stats_cursor() as c:
                    logger.info('Deleting data from table "%s" for day %s, job %s', self.TABLE_NAME, date, self.job_id)
                    sql, params = redshift.prepare_daily_delete_query(self.TABLE_NAME, date, self.account_id)
                    c.execute(sql, params)

                    # generate csv in transaction as it needs data created in it
                    s3_path = os.path.join(
                        constants.SPARK_S3_PREFIX, self.job_id, self.TABLE_NAME, date.strftime("%Y-%m-%d") + ".csv"
                    )
                    s3.upload_csv(s3_path, partial(self.generate_rows, c, date))

                    logger.info('Copying CSV to table "%s" for day %s, job %s', self.TABLE_NAME, date, self.job_id)
                    sql, params = redshift.prepare_copy_query(s3_path, self.TABLE_NAME)
                    c.execute(sql, params)

        s3_path = os.path.join(constants.SPARK_S3_PREFIX, self.job_id, self.TABLE_NAME) + "/*.csv"
        self.spark_session.run_file(
            "load_csv_from_s3_to_table.py.tmpl",
            table=self.TABLE_NAME,
            s3_bucket=settings.S3_BUCKET_STATS,
            s3_path=s3_path,
            schema=spark.generate_schema(self.SPARK_COLUMNS),
        )

        # cache
        self.spark_session.run_file("cache_table.py.tmpl", table=self.TABLE_NAME)

    def generate_rows(self, cursor, date):
        for _, row, conversions_tuple in self.master_view.get_postclickstats(cursor, date):
            conversions = conversions_tuple[0]
            postclick_source = conversions_tuple[1]

            if conversions:
                conversions = json.loads(conversions)

                for slug, hits in conversions.items():
                    slug = helpers.get_conversion_prefix(postclick_source, slug)
                    yield tuple(list(row)[:8] + [slug, hits])
