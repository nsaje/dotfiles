import influx

import core.entity

import automation.campaignstop
import automation.campaignstop.constants

from utils.command_helpers import ExceptionCommand
from utils import dates_helper


class Command(ExceptionCommand):

    @influx.timer('campaignstop.selection_job')
    def handle(self, *args, **options):
        campaigns = core.entity.Campaign.objects.filter(
            real_time_campaign_stop=True,
            campaignstopstate__almost_depleted=False,
            campaignstopstate__state=automation.campaignstop.constants.CampaignStopState.ACTIVE,
            campaignstopstate__max_allowed_end_date__gte=dates_helper.local_today(),
        )
        automation.campaignstop.mark_almost_depleted_campaigns(campaigns)
