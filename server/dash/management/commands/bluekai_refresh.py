import logging

import utils.slack
from dash.features.bluekai.service import maintenance
from utils.command_helpers import ExceptionCommand

logger = logging.getLogger(__name__)


class Command(ExceptionCommand):
    help = "Refresh and cross check BlueKai categories"

    def add_arguments(self, parser):
        parser.add_argument("--verbose", dest="verbose", action="store_true", help="Display output")
        parser.add_argument("--slack", dest="slack", action="store_true", help="Notify via slack")

    def _log_error_message(self, options, message, type=utils.slack.MESSAGE_TYPE_WARNING):
        if message and options.get("verbose"):
            self.stdout.write("{}\n".format(message))
        if message and options.get("slack"):
            utils.slack.publish(message, msg_type=type, username=utils.slack.USER_BLUEKAI_MONITORING)

    def _cross_check_audience_categories(self, options):
        message = maintenance.cross_check_audience_categories()
        self._log_error_message(options, message)

    def _check_campaign_status(self, options):
        message = maintenance.check_campaign_status()
        self._log_error_message(options, message, type=utils.slack.MESSAGE_TYPE_CRITICAL)

    def handle(self, *args, **options):
        # maintenance.refresh_bluekai_categories()
        self._cross_check_audience_categories(options)
        self._check_campaign_status(options)
