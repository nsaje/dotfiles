import logging
import datetime

from dash.features.contentupload.upload import clean_up_old_in_progress_batches
from utils.command_helpers import ExceptionCommand
from utils import dates_helper

logger = logging.getLogger(__name__)

IN_PROGRESS_MINUTES = 15


class Command(ExceptionCommand):
    help = "Set old unprocessed batches to FAILED."

    def handle(self, *args, **options):
        failed_count = clean_up_old_in_progress_batches(
            created_before=dates_helper.utc_now() - datetime.timedelta(minutes=IN_PROGRESS_MINUTES)
        )

        logger.info('Moved %s batches to FAILED.', failed_count)
