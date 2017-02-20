import logging
import sys

from optparse import make_option

from automation import campaign_stop
import dash.models
from utils.command_helpers import ExceptionCommand

logger = logging.getLogger(__name__)


class Command(ExceptionCommand):
    option_list = ExceptionCommand.option_list + (
        make_option('-c', '--campaign', help='campaign id'),
    )

    def handle(self, *args, **options):

        if not options['campaign']:
            logger.info('Campaign id not provided. Exiting...')
            sys.exit(0)

        campaign = dash.models.Campaign.objects.get(id=int(options['campaign']))
        campaign_settings = campaign.get_current_settings()
        if not campaign_settings.automatic_campaign_stop or campaign_settings.landing_mode:
            logger.info('Campaign already in landing or can\'t be put into landing mode. Exiting...')
            sys.exit(0)

        campaign_stop.switch_low_budget_campaigns_to_landing_mode([campaign], pagerduty_on_fail=False)
