import utils.slack
from dash.features.bluekai.service import maintenance
from utils import zlogging
from utils.command_helpers import Z1Command

logger = zlogging.getLogger(__name__)


class BluekaiMonitoringException(Exception):
    pass


class Command(Z1Command):
    help = "Refresh bluekai categories by using only active ones"

    def add_arguments(self, parser):
        parser.add_argument("--verbose", dest="verbose", action="store_true", help="Display output")
        parser.add_argument("--slack", dest="slack", action="store_true", help="Notify via slack")

    def handle(self, *args, **options):
        maintenance.update_dynamic_audience()

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
