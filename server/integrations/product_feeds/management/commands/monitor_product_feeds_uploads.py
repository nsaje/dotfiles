import datetime

import dash.constants
from integrations.product_feeds.models import SyncAttempt
from utils import slack
from utils.command_helpers import Z1Command


class Command(Z1Command):
    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        sync_attempts_in_last_6h = SyncAttempt.objects.filter(
            timestamp__range=((datetime.datetime.now() - datetime.timedelta(hours=3)), datetime.datetime.now()),
            batches__isnull=False,
            dry_run=False,
        )
        if not sync_attempts_in_last_6h:
            slack.publish(
                "No ads were uploaded from product feeds  in the last 6h. ad groups",
                username="product feed",
                msg_type=slack.MESSAGE_TYPE_WARNING,
            )
            return

        for sync_attempt in sync_attempts_in_last_6h:
            for batch in sync_attempt.batches:
                if batch.status != dash.constants.UploadBatchStatus.DONE:
                    msg = "Batch upload for product feed {} is in status {} for ad groups {}".format(
                        sync_attempt.product_feed.name,
                        batch.status,
                        ", ".join(sync_attempt.product_feed.ad_groups.values_list("id", flat=True)),
                    )
                    slack.publish(msg, username="product feed", msg_type=slack.MESSAGE_TYPE_WARNING)
