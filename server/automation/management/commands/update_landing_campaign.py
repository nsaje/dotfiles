import logging
import sys

from optparse import make_option

from automation import campaign_stop
import dash.models
from utils.command_helpers import ExceptionCommand

logger = logging.getLogger(__name__)


class Command(ExceptionCommand):
    option_list = ExceptionCommand.option_list + (
        make_option('--campaign', '-c', 'campaign id'),
    )

    def handle(self, *args, **options):

        if not options['campaign']:
            logger.info('Campaign id not provided. Exiting...')
            sys.exit(0)

        campaign = dash.models.Campaign.objects.get(id=int(options['campaign']))
        if not campaign.is_in_landing():
            logger.info('Campaign not landing. Exiting...')
            sys.exit(0)

        campaign_stop.update_landing_campaigns([campaign], pagerduty_on_fail=False)
