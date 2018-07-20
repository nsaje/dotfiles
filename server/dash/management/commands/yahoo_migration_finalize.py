import logging

import core.features.yahoo_accounts
from utils.command_helpers import ExceptionCommand

logger = logging.getLogger(__name__)


class Command(ExceptionCommand):
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
