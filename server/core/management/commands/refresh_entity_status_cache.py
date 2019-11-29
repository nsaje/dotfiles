import core.features.entity_status.service
from utils.command_helpers import Z1Command


class Command(Z1Command):
    help = "Refresh entity status cache"

    def handle(self, *args, **options):
        core.features.entity_status.service.refresh_accounts_statuses_cache()
