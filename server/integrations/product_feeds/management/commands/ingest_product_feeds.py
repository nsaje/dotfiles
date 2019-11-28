import concurrent.futures

from core.common.entity_limits import EntityLimitExceeded
from integrations.product_feeds import constants
from integrations.product_feeds.models import ProductFeed
from utils.command_helpers import Z1Command


class Command(Z1Command):
    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            dest="dry_run",
            action="store_true",
            default=False,
            help="Will not stop ads or upload new ones.",
        )

    def handle(self, *args, **options):
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            for product_feed in ProductFeed.objects.filter(status=constants.FeedStatus.ENABLED):
                try:
                    executor.map(product_feed.pause_and_archive_ads(dry_run=options["dry_run"]))
                    executor.map(product_feed.ingest_and_create_ads(dry_run=options["dry_run"]))
                except (EntityLimitExceeded, Exception):
                    continue
