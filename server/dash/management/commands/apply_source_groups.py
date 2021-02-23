import datetime
import logging

from utils.command_helpers import Z1Command

logger = logging.getLogger(__name__)

DEFAULT_MODE = 1
BATCH_SIZE = 1000
POOL_SIZE = 10


# TODO: SRCGRP: MIGRATION: remove after all agencies migrated
class Command(Z1Command):
    help = "Apply source grouping to an agency"

    def add_arguments(self, parser):
        parser.add_argument(dest="agency_id", type=int, help="ID of the migrated agency")
        parser.add_argument(
            "--create-entities", dest="create_entities", action="store_true", help="Create migrated entities"
        )
        parser.add_argument("--created_dt", type=datetime.datetime.fromisoformat, default=None)
        parser.add_argument(
            "--mode", type=int, default=DEFAULT_MODE, help="1: bid modifiers, 2: publisher groups, 3: MSN, 4: all"
        )
        parser.add_argument("--batch-size", dest="batch_size", default=BATCH_SIZE, type=int, help="Batch size")
        parser.add_argument("--use-pool", dest="use_pool", action="store_true", help="Use thread pool")
        parser.add_argument("--pool-size", dest="pool_size", type=int, default=POOL_SIZE, help="Thread pool size")
        parser.add_argument("--log-ids", dest="log_ids", action="store_true", help="Log entity IDs for changes")

    def handle(self, *args, **options):
        # agency_id = options["agency_id"]
        create_entities = options.get("create_entities", False)
        # created_dt = options.get("created_dt", None)
        mode = options.get("mode", DEFAULT_MODE)
        # batch_size = options.get("batch_size", BATCH_SIZE)
        use_pool = options.get("use_pool", False)
        # pool_size = options.get("pool_size", POOL_SIZE)
        # log_ids = options.get("log_ids", False)

        if use_pool:
            self.stdout.write(self.style.SUCCESS("Processing using thread pool"))

        if create_entities:
            self.stdout.write(self.style.WARNING("The changes will be applied to database"))

        if mode == 1:
            pass

        elif mode == 2:
            pass

        elif mode == 3:
            pass

        elif mode == 4:
            pass
