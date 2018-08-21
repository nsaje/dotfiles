import logging
import datetime

from utils.command_helpers import ExceptionCommand

import etl.redshift
from etl import refresh

from utils import dates_helper

logger = logging.getLogger(__name__)


class Command(ExceptionCommand):
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
            logger.info("Copying table %s into %s" % (table, to_db_alias))
            s3_path = etl.redshift.unload_table(job_id, table, date_from, date_to)
            etl.redshift.update_table_from_s3(to_db_alias, s3_path, table, date_from, date_to)
