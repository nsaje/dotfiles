import automation.rules
from utils import metrics_compat
from utils import zlogging
from utils.command_helpers import Z1Command

logger = zlogging.getLogger(__name__)


class Command(Z1Command):
    help = "Execute automation rules actions on affected ad groups."

    @metrics_compat.timer("automation.rules.run_rules_job")
    def handle(self, *args, **options):
        logger.info("Executing automation rules...")
        automation.rules.execute_rules_daily_run()
