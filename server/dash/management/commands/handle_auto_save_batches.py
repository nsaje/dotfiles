import datetime
import logging

from dash.features.contentupload import upload
from utils.command_helpers import ExceptionCommand
from utils import dates_helper

logger = logging.getLogger(__name__)


AUTO_SAVE_HOURS = 2


class Command(ExceptionCommand):
    help = "Handle auto_save batches in progress"

    def handle(self, *args, **options):
        upload.handle_auto_save_batches(
            created_after=dates_helper.utc_now() - datetime.timedelta(hours=AUTO_SAVE_HOURS)
        )
