import structlog

import backtosql
import dash.models
from etl import redshift
from etl import s3
from redshiftapi import db

from .materialize import Materialize

logger = structlog.get_logger(__name__)


class MVHelpersAdGroupStructure(Materialize):
    """
    Helper view that puts ad group structure (campaign id, account id, agency id) into redshift. Its than
    used to construct the mv_master view.
    """

    TABLE_NAME = "mvh_adgroup_structure"
    IS_TEMPORARY_TABLE = True

    def generate(self, **kwargs):
        s3_path = s3.upload_csv(self.TABLE_NAME, self.date_to, self.job_id, self.generate_rows)

        with db.get_write_stats_transaction():
            with db.get_write_stats_cursor() as c:
                sql = backtosql.generate_sql("etl_create_temp_table_mvh_adgroup_structure.sql", None)
                c.execute(sql)

                logger.info("Copying CSV to table", table=self.TABLE_NAME, job=self.job_id)
                sql, params = redshift.prepare_copy_query(s3_path, self.TABLE_NAME)
                c.execute(sql, params)
                logger.info("Copied CSV to table", table=self.TABLE_NAME, job=self.job_id)

    def generate_rows(self):
        ad_groups = dash.models.AdGroup.objects.select_related("campaign", "campaign__account").all()
        if self.account_id:
            ad_groups = ad_groups.filter(campaign__account_id=self.account_id)

        for ad_group in ad_groups:
            yield (ad_group.campaign.account.agency_id, ad_group.campaign.account_id, ad_group.campaign_id, ad_group.id)
