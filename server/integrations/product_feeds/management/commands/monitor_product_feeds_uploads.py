import datetime

import dash.constants
from integrations.product_feeds.models import SyncAttempt
from utils import slack
from utils.command_helpers import Z1Command

HOURS = 6


class Command(Z1Command):
    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        previous_sync_attempts = SyncAttempt.objects.filter(
            timestamp__range=((datetime.datetime.now() - datetime.timedelta(hours=HOURS)), datetime.datetime.now()),
            batches__isnull=False,
            dry_run=False,
        )
        if not previous_sync_attempts:
            slack.publish(
                "No ads were uploaded from product feeds  in the last {}h. ad groups".format(HOURS),
                username="product feed",
                msg_type=slack.MESSAGE_TYPE_WARNING,
            )
            return

        for sync_attempt in previous_sync_attempts:
            for batch in sync_attempt.batches.all():
                if batch.status != dash.constants.UploadBatchStatus.DONE:
                    msg = "Batch upload for product feed {} is in status {} for ad groups {}. #{}".format(
                        sync_attempt.product_feed.name,
                        batch.status,
                        ", ".join([str(i) for i in sync_attempt.product_feed.ad_groups.values_list("id", flat=True)]),
                        sync_attempt.id,
                    )
                    slack.publish(msg, username="product feed", msg_type=slack.MESSAGE_TYPE_WARNING)
