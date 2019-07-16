import logging

import utils.slack
from dash.features.bluekai.service import maintenance
from utils.command_helpers import Z1Command

logger = logging.getLogger(__name__)


class BluekaiMonitoringException(Exception):
    pass


class Command(Z1Command):
    help = "Refresh and cross check BlueKai categories"

    def add_arguments(self, parser):
        parser.add_argument("--verbose", dest="verbose", action="store_true", help="Display output")
        parser.add_argument("--slack", dest="slack", action="store_true", help="Notify via slack")

    def _log_error_message(self, options, message, type=utils.slack.MESSAGE_TYPE_WARNING):
        if message and options.get("verbose"):
            self.stdout.write("{}\n".format(message))
        if message and options.get("slack"):
            utils.slack.publish(
                message,
                msg_type=type,
                username=utils.slack.USER_BLUEKAI_MONITORING,
                channel=utils.slack.CHANNEL_RND_Z1_ALERTS_AUX,
            )

    def _cross_check_audience_categories(self, options):
        message = maintenance.cross_check_audience_categories()
        self._log_error_message(options, message)

    def _check_campaign_status(self, options):
        running, bluekai_campaign = maintenance.is_bluekai_campaign_running()
        if not running:
            message = (
                'Campaign "{}" (id: {}) status is set to "{}", not "active". '
                "The campaign data may not be syncing. Check https://partner.bluekai.com/rails/campaigns/{}.".format(
                    bluekai_campaign["name"], bluekai_campaign["id"], bluekai_campaign["status"], bluekai_campaign["id"]
                )
            )
            self._log_error_message(options, message, type=utils.slack.MESSAGE_TYPE_CRITICAL)
            raise BluekaiMonitoringException("Bluekai campaign is not running")

    def handle(self, *args, **options):
        # maintenance.refresh_bluekai_categories()
        self._cross_check_audience_categories(options)
        self._check_campaign_status(options)
