import logging

from integrations.bizwire.internal import monitor
from utils.command_helpers import Z1Command

logger = logging.getLogger(__name__)


class Command(Z1Command):
    def add_arguments(self, parser):
        parser.add_argument("--send-emails", dest="send_emails", action="store_true")

    def handle(self, *args, **options):
        should_send_emails = options.get("send_emails")
        monitor.run_hourly_job(should_send_emails=should_send_emails)
