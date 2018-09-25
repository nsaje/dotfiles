import logging
import os.path

from django.conf import settings

from etl import constants
from etl import redshift
from .materialize import Materialize

logger = logging.getLogger(__name__)


class MasterView(Materialize):
    """
    Represents breakdown by all dimensions available. It containts traffic, postclick, conversions
    and tochpoint conversions data.

    NOTE: It excludes outbrain publishers as those are currently not linked to content ads and so
    breakdown by publisher and content ad is not possible for them.
    """

    TABLE_NAME = "mv_master"

    def generate(self, **kwargs):
        # load to redshift
        s3_path = os.path.join(constants.SPARK_S3_PREFIX, self.job_id, self.TABLE_NAME) + "/"
        self.spark_session.run_file(
            "export_table_to_json_s3.py.tmpl",
            table=self.TABLE_NAME,
            s3_bucket=settings.S3_BUCKET_STATS,
            s3_path=s3_path,
        )
        redshift.update_table_from_s3_json(s3_path, self.TABLE_NAME, self.date_from, self.date_to, self.account_id)
