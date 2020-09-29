import automation.campaignstop
import automation.campaignstop.constants
import core.models
from utils import dates_helper
from utils import metrics_compat
from utils import zlogging
from utils.command_helpers import Z1Command

logger = zlogging.getLogger(__name__)


class Command(Z1Command):
    @metrics_compat.timer("campaignstop.job_run", campaignstop_job="selection")
    def handle(self, *args, **options):
        campaigns = core.models.Campaign.objects.filter(
            real_time_campaign_stop=True,
            campaignstopstate__state=automation.campaignstop.constants.CampaignStopState.ACTIVE,
            campaignstopstate__max_allowed_end_date__gte=dates_helper.local_today(),
        )
        automation.campaignstop.mark_almost_depleted_campaigns(campaigns)
        metrics_compat.gauge("campaignstop.selection_job_campaigns", len(campaigns))
        metrics_compat.incr("campaignstop.job_completed", 1, campaignstop_job="selection")
        logger.info(f"Selection job finished on {len(campaigns)} campaigns")
