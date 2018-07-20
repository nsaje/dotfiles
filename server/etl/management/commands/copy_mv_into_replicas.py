import logging
import datetime

from utils.command_helpers import ExceptionCommand

from etl import refresh_k1

from utils import dates_helper

logger = logging.getLogger(__name__)


class Command(ExceptionCommand):
    help = "Copy materialized views for the last N days into the write replicas configured in settings"

    def add_arguments(self, parser):
        parser.add_argument("num_days", type=int, help="Copy data for the last N days")

    def handle(self, *args, **options):
        num_days = options["num_days"]
        date_to = dates_helper.local_today()
        date_from = date_to - datetime.timedelta(days=num_days)

        job_id = refresh_k1.generate_job_id(None)
        refresh_k1.unload_and_copy_into_replicas(
            refresh_k1.MATERIALIZED_VIEWS, job_id, date_from, date_to, skip_vacuum=True, skip_analyze=True
        )
