import logging

import core.features.yahoo_accounts
from utils.command_helpers import ExceptionCommand

logger = logging.getLogger(__name__)


class Command(ExceptionCommand):
    help = 'Finalize yahoo account migration by changing all external source ids'

    def add_arguments(self, parser):
        parser.add_argument('account_id', type=int)

    def handle(self, *args, **options):
        core.features.yahoo_accounts.finalize_migration(options['account_id'])
