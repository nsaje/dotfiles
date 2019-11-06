import datetime

import etl.redshift
from etl import refresh
from utils import dates_helper
from utils import zlogging
from utils.command_helpers import Z1Command

logger = zlogging.getLogger(__name__)


class Command(Z1Command):
    help = (
        "Copy raw tables to a specified Redshift cluster. NOTE: audience_report and pixie_sample tables are not copied."
    )

    def add_arguments(self, parser):
        parser.add_argument("to_db_alias", type=str)
        parser.add_argument("num_days", type=int)

    def handle(self, *args, **options):
        tables = ["conversions", "postclickstats", "outbrainpublisherstats", "stats", "supply_stats"]

        to_db_alias = options["to_db_alias"]
        num_days = options["num_days"]
        date_to = dates_helper.local_today()
        date_from = date_to - datetime.timedelta(days=num_days)

        job_id = refresh.generate_job_id(None)
        for table in tables:
            logger.info("Copying table", table=table, into=to_db_alias)
            s3_path = etl.redshift.unload_table(job_id, table, date_from, date_to)
            etl.redshift.update_table_from_s3(to_db_alias, s3_path, table, date_from, date_to)
