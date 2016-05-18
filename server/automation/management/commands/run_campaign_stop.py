import logging

from automation import campaign_stop
from utils.command_helpers import ExceptionCommand

logger = logging.getLogger(__name__)


class Command(ExceptionCommand):
    def handle(self, *args, **options):
        campaign_stop.run_job()
