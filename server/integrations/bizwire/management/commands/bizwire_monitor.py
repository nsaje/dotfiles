import logging

from integrations.bizwire.internal import monitor
from utils.command_helpers import ExceptionCommand

logger = logging.getLogger(__name__)


class Command(ExceptionCommand):
    def handle(self, *args, **options):
        monitor.run_hourly_job()
