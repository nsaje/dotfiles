import automation.campaignstop
from utils import metrics_compat
from utils import zlogging
from utils.command_helpers import Z1Command

logger = zlogging.getLogger(__name__)


class Command(Z1Command):
    @metrics_compat.timer("campaignstop.job_run", job="simple")
    def handle(self, *args, **options):
        logger.info("Start: Stopping and notifying depleted budget campaigns.")
        automation.campaignstop.stop_and_notify_depleted_budget_campaigns()
        logger.info("Finish: Stopping and notifying depleted budget campaigns.")

        logger.info("Start: Notifying campaigns with depleting budget.")
        automation.campaignstop.notify_depleting_budget_campaigns()
        logger.info("Finish: Notifying campaigns with depleting budget.")
        metrics_compat.incr("campaignstop.job_completed", 1, job="simple")
