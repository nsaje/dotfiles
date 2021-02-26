import backtosql
import core.features.source_groups
import dash.models
from etl import helpers
from etl import redshift
from etl import s3
from redshiftapi import db
from utils import zlogging

from .materialize import Materialize

logger = zlogging.getLogger(__name__)


class MVHelpersSource(Materialize):

    TABLE_NAME = "mvh_source"
    IS_TEMPORARY_TABLE = True

    def generate(self, **kwargs):
        s3_path = s3.upload_csv(self.TABLE_NAME, self.date_to, self.job_id, self.generate_rows)

        with db.get_write_stats_transaction():
            with db.get_write_stats_cursor() as c:
                sql = backtosql.generate_sql("etl_create_temp_table_mvh_source.sql", None)
                c.execute(sql)

                logger.info("Copying CSV to table", table=self.TABLE_NAME, job=self.job_id)
                sql, params = redshift.prepare_copy_query(s3_path, self.TABLE_NAME)
                c.execute(sql, params)
                logger.info("Copied CSV to table", table=self.TABLE_NAME, job=self.job_id)

    def generate_rows(self):
        sources = dash.models.Source.objects.all().order_by("id")

        grouped_sources = core.features.source_groups.get_source_id_group_id_mapping()
        for source in sources:
            yield (
                source.id,
                helpers.extract_source_slug(source.bidder_slug),
                source.bidder_slug,
                grouped_sources.get(source.id) or source.id,
            )
