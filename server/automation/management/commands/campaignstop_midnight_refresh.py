import influx

from django.db.models import Q

import automation.campaignstop
import core.entity

from utils.command_helpers import ExceptionCommand
from utils import dates_helper


class Command(ExceptionCommand):

    def add_arguments(self, parser):
        parser.add_argument('--check-time', dest='check_time', action='store_true',
                            help="Check if it's local hour before midnight.")

    def handle(self, *args, **options):
        if options.get('check_time') and not dates_helper.local_now().hour == 23:
            return

        self._run_job()

    @influx.timer('campaignstop.job_run', job='midnight_refresh')
    def _run_job(self):
        local_tomorrow = dates_helper.day_after(dates_helper.local_today())
        rechecked_campaigns = core.entity.Campaign.objects.filter(
            Q(
                campaignstopstate__state=automation.campaignstop.constants.CampaignStopState.STOPPED,
                campaignstopstate__max_allowed_end_date__gte=local_tomorrow
            )
        )
        automation.campaignstop.refresh_realtime_data(rechecked_campaigns)
