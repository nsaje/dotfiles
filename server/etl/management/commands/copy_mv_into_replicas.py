import datetime

import structlog

from etl import materialize
from etl import refresh
from utils import dates_helper
from utils.command_helpers import Z1Command

logger = structlog.get_logger(__name__)


class Command(Z1Command):
    help = "Copy materialized views for the last N days into the write replicas configured in settings"

    def add_arguments(self, parser):
        parser.add_argument("num_days", type=int, help="Copy data for the last N days")

    def handle(self, *args, **options):
        num_days = options["num_days"]
        date_to = dates_helper.local_today()
        date_from = date_to - datetime.timedelta(days=num_days)

        job_id = refresh.generate_job_id(None)
        refresh.unload_and_copy_into_replicas(materialize.MATERIALIZED_VIEWS, job_id, date_from, date_to)
