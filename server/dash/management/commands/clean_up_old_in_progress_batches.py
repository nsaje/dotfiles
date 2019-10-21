import datetime

import structlog

from dash.features.contentupload.upload import clean_up_old_in_progress_batches
from utils import dates_helper
from utils.command_helpers import Z1Command

logger = structlog.get_logger(__name__)

IN_PROGRESS_MINUTES = 15


class Command(Z1Command):
    help = "Set old unprocessed batches to FAILED."

    def handle(self, *args, **options):
        failed_count = clean_up_old_in_progress_batches(
            created_before=dates_helper.utc_now() - datetime.timedelta(minutes=IN_PROGRESS_MINUTES)
        )

        logger.info("Moved batches to FAILED.", failed_count=failed_count)
