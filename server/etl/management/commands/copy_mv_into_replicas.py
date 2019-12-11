import datetime

from django.conf import settings

from etl import materialize
from etl import refresh
from utils import dates_helper
from utils import zlogging
from utils.command_helpers import Z1Command

logger = zlogging.getLogger(__name__)
HOT_CLUSTER_MAX_DAYS = settings.STATS_DB_HOT_CLUSTER_MAX_DAYS


class Command(Z1Command):
    help = "Copy materialized views for the last N days into the replicas configured in settings"

    def add_arguments(self, parser):
        parser.add_argument("num_days", type=int, help="Copy data for the last N days")

    def handle(self, *args, **options):
        num_days = options["num_days"]
        if num_days > HOT_CLUSTER_MAX_DAYS:
            raise ValueError(
                "Number of days '{}' must be lower or equal to the hot cluster max days '{}'".format(
                    num_days, HOT_CLUSTER_MAX_DAYS
                )
            )

        date_to = dates_helper.local_today()
        date_from = date_to - datetime.timedelta(days=num_days)

        job_id = refresh.generate_job_id(None)
        refresh.unload_and_copy_into_replicas(materialize.MATERIALIZED_VIEWS, job_id, date_from, date_to)
