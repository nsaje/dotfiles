import automation.rules
from utils import metrics_compat
from utils import zlogging
from utils.command_helpers import Z1Command

logger = zlogging.getLogger(__name__)


class Command(Z1Command):
    help = "Execute specified automation rule."

    def add_arguments(self, parser):
        parser.add_argument("rule_id", type=int)

    @metrics_compat.timer("automation.rules.run_rules_job")
    def handle(self, *args, **options):
        self.stdout.write(f"Executing rule with id: {options['rule_id']}")
        automation.rules.execute_rules([automation.rules.Rule.objects.get(id=options["rule_id"])])
