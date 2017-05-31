import logging

from dash.features.bluekai.service import maintenance
from utils.command_helpers import ExceptionCommand
import utils.slack

logger = logging.getLogger(__name__)


class Command(ExceptionCommand):
    help = 'Refresh and cross check BlueKai categories'

    def add_arguments(self, parser):
        parser.add_argument('--verbose', dest='verbose', action='store_true',
                            help='Display output')
        parser.add_argument('--slack', dest='slack', action='store_true',
                            help='Notify via slack')

    def handle(self, *args, **options):
        maintenance.refresh_bluekai_categories()
        message = maintenance.cross_check_audience_categories()
        if message and options.get('verbose'):
            self.stdout.write(u'{}\n'.format(message))
        if message and options.get('slack'):
            utils.slack.publish(
                message,
                msg_type=utils.slack.MESSAGE_TYPE_WARNING,
                username='BlueKai Categories Sync'
            )
