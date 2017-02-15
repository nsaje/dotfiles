import logging
import utils.email_helper
from utils.command_helpers import set_logger_verbosity, ExceptionCommand

logger = logging.getLogger(__name__)


class Command(ExceptionCommand):

    help = "Sends weekly client report email"

    def handle(self, *args, **options):
        set_logger_verbosity(logger, options)
        utils.email_helper.send_weekly_client_report_email()
