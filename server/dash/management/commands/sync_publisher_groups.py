from core.features.publisher_groups import sync
from utils.command_helpers import Z1Command


class Command(Z1Command):
    help = "Sync publisher groups to bidder."

    def handle(self, *args, **options):
        sync.sync_publisher_groups()
