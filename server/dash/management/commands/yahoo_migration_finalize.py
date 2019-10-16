import core.features.yahoo_accounts
import structlog
from utils.command_helpers import Z1Command

logger = structlog.get_logger(__name__)


class Command(Z1Command):
    help = "Finalize yahoo account migration by changing all external source ids"

    def add_arguments(self, parser):
        parser.add_argument("account_id", type=int)
        parser.add_argument("--direct-migration", action="store_true", dest="direct_migration")
        parser.add_argument("--currency")
        parser.add_argument("--advertiser_id")

    def handle(self, *args, **options):
        core.features.yahoo_accounts.finalize_migration(
            options["account_id"],
            options.get("direct_migration"),
            advertiser_id=options.get("advertiser_id"),
            currency=options.get("currency"),
        )
