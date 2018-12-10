import influx

import automation.campaignstop
import automation.campaignstop.constants
import core.models
from utils import dates_helper
from utils.command_helpers import ExceptionCommand


class Command(ExceptionCommand):
    @influx.timer("campaignstop.job_run", job="main")
    def handle(self, *args, **options):
        campaigns = core.models.Campaign.objects.filter(
            real_time_campaign_stop=True,
            campaignstopstate__almost_depleted=True,
            campaignstopstate__state=automation.campaignstop.constants.CampaignStopState.ACTIVE,
        ).select_related("campaignstopstate")
        automation.campaignstop.update_campaigns_state(campaigns)

        self._monitor(campaigns)

    def _monitor(self, campaigns):
        campaigns = list(campaigns)
        influx.gauge("campaignstop.main_job_campaigns", len(campaigns))
        for campaign in campaigns:
            if not campaign.campaignstopstate.almost_depleted_marked_dt:
                continue
            timedelta_since_marked = dates_helper.utc_now() - campaign.campaignstopstate.almost_depleted_marked_dt
            influx.gauge(
                "campaignstop.main_job_campaign_time",
                timedelta_since_marked.total_seconds(),
                campaign_id=str(campaign.id),
            )
