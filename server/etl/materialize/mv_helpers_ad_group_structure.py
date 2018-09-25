import logging
import os.path

from django.conf import settings

import dash.models

from etl import constants
from etl import s3
from etl import spark
from .materialize import Materialize

logger = logging.getLogger(__name__)


class MVHelpersAdGroupStructure(Materialize):
    """
    Helper view that puts ad group structure (campaign id, account id, agency id) into redshift. Its than
    used to construct the mv_master view.
    """

    TABLE_NAME = "mvh_adgroup_structure"
    IS_TEMPORARY_TABLE = True
    SPARK_COLUMNS = [
        spark.Column("agency_id", "int"),
        spark.Column("account_id", "int"),
        spark.Column("campaign_id", "int"),
        spark.Column("ad_group_id", "int"),
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
        ad_groups = dash.models.AdGroup.objects.select_related("campaign", "campaign__account").all()
        if self.account_id:
            ad_groups = ad_groups.filter(campaign__account_id=self.account_id)

        for ad_group in ad_groups:
            yield (ad_group.campaign.account.agency_id, ad_group.campaign.account_id, ad_group.campaign_id, ad_group.id)
