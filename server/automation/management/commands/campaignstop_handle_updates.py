import automation.campaignstop
from utils import metrics_compat
from utils.command_helpers import Z1Command

PARALLELISM = 20


class Command(Z1Command):
    @metrics_compat.timer("campaignstop.job_run", job="handle_updates")
    def handle(self, *args, **options):
        automation.campaignstop.handle_updates_parallel(PARALLELISM)
        metrics_compat.incr("campaignstop.job_completed", 1, job="handle_updates")
