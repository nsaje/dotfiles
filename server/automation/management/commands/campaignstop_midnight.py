from django.db.models import Q

import automation.campaignstop
import core.models
import structlog
from utils import dates_helper
from utils import metrics_compat
from utils.command_helpers import Z1Command

logger = structlog.get_logger(__name__)


class Command(Z1Command):
    def add_arguments(self, parser):
        parser.add_argument(
            "--check-time", dest="check_time", action="store_true", help="Check if it's local midnight."
        )

    def handle(self, *args, **options):
        if options.get("check_time") and not dates_helper.local_now().hour == 0:
            return

        self._run_midnight_job()
        metrics_compat.incr("campaignstop.job_completed", 1, job="midnight")

    @metrics_compat.timer("campaignstop.job_run", job="midnight")
    def _run_midnight_job(self):
        logger.info("Updating end dates for every campaign")
        automation.campaignstop.update_campaigns_end_date()
        self._correct_states()

    def _correct_states(self):
        campaigns_yesterday = core.models.Campaign.objects.filter(
            Q(
                campaignstopstate__state=automation.campaignstop.constants.CampaignStopState.STOPPED,
                campaignstopstate__max_allowed_end_date__gte=dates_helper.local_today(),
            )
            | Q(
                campaignstopstate__state=automation.campaignstop.constants.CampaignStopState.ACTIVE,
                campaignstopstate__max_allowed_end_date__lt=dates_helper.local_today(),
            )
        )
        logger.info(
            "Correcting campaign states for %s campaigns that were stopped on the previous day",
            campaigns_yesterday.count(),
        )
        automation.campaignstop.update_campaigns_state(campaigns_yesterday)
        automation.campaignstop.mark_almost_depleted_campaigns(campaigns_yesterday)
