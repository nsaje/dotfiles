import logging

import utils.email_helper
from utils.command_helpers import ExceptionCommand
from utils.command_helpers import set_logger_verbosity

logger = logging.getLogger(__name__)


class Command(ExceptionCommand):

    help = "Sends daily management report email"

    def handle(self, *args, **options):
        set_logger_verbosity(logger, options)
        utils.email_helper.send_daily_management_report_email()
