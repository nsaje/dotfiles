import influx

import automation.campaignstop
import core.entity

from utils.command_helpers import ExceptionCommand
from utils import dates_helper


class Command(ExceptionCommand):

    def add_arguments(self, parser):
        parser.add_argument('--check-time', dest='check_time', action='store_true',
                            help="Check if it's local midnight.")

    @influx.timer('campaignstop.job_run', job='midnight')
    def handle(self, *args, **options):
        if options.get('check_time') and not dates_helper.local_now().hour == 0:
            return
        automation.campaignstop.update_campaigns_end_date()

        campaigns_today = core.entity.Campaign.objects.filter(
            campaignstopstate__state=automation.campaignstop.constants.CampaignStopState.STOPPED,
            campaignstopstate__max_allowed_end_date__gte=dates_helper.local_today()
        )
        automation.campaignstop.update_campaigns_state(campaigns_today)
        automation.campaignstop.mark_almost_depleted_campaigns(campaigns_today)
