import core.features.creatives
from utils import zlogging
from utils.command_helpers import Z1Command

logger = zlogging.getLogger(__name__)


class Command(Z1Command):
    help = "Migrate ContentAd to Creative"

    def add_arguments(self, parser):
        parser.add_argument("--account_id", type=int)
        parser.add_argument("--offset", type=int, default=0)
        parser.add_argument("--limit", type=int, default=1000)

    def handle(self, *args, **options):
        core.features.creatives.migrate_for_account(
            options.get("account_id"), offset=options.get("offset"), limit=options.get("limit")
        )
