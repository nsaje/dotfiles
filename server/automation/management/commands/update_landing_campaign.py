import logging
import sys

from automation import campaign_stop
import dash.models
from utils.command_helpers import ExceptionCommand

logger = logging.getLogger(__name__)


class Command(ExceptionCommand):

    def add_arguments(self, parser):
        parser.add_argument('-c', '--campaign', help='campaign id')

    def handle(self, *args, **options):

        if not options['campaign']:
            logger.info('Campaign id not provided. Exiting...')
            sys.exit(0)

        campaign = dash.models.Campaign.objects.get(id=int(options['campaign']))
        if not campaign.is_in_landing():
            logger.info('Campaign not landing. Exiting...')
            sys.exit(0)

        campaign_stop.update_campaigns_in_landing([campaign], pagerduty_on_fail=False)
