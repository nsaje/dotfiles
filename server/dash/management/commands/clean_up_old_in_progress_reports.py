import datetime
import logging

from dash.features.reports.reports import clean_up_old_in_progress_reports
from utils import dates_helper
from utils.command_helpers import Z1Command

logger = logging.getLogger(__name__)

IN_PROGRESS_MINUTES = 60


class Command(Z1Command):
    help = "Set old unprocessed reports to FAILED and notify users."

    def handle(self, *args, **options):
        failed_count = clean_up_old_in_progress_reports(
            created_before=dates_helper.utc_now() - datetime.timedelta(minutes=IN_PROGRESS_MINUTES)
        )
        logger.info("Moved %s reports to FAILED.", failed_count)
