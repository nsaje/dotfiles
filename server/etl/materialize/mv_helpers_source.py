import logging
import os.path

from django.conf import settings

import dash.models

from etl import constants
from etl import helpers
from etl import s3
from etl import spark
from .materialize import Materialize

logger = logging.getLogger(__name__)


class MVHelpersSource(Materialize):

    TABLE_NAME = "mvh_source"
    IS_TEMPORARY_TABLE = True
    SPARK_COLUMNS = [
        spark.Column("source_id", "int"),
        spark.Column("bidder_slug", "string"),
        spark.Column("clean_slug", "string"),
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

    def generate_rows(self):
        sources = dash.models.Source.objects.all().order_by("id")

        for source in sources:
            yield (source.id, helpers.extract_source_slug(source.bidder_slug), source.bidder_slug)
