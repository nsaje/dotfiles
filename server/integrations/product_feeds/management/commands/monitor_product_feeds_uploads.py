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

        messages = []
        for sync_attempt in previous_sync_attempts:
            if sync_attempt.batches.filter(
                status__in=[dash.constants.UploadBatchStatus.FAILED, dash.constants.UploadBatchStatus.CANCELLED]
            ).exists():
                msg = "upload for product feed {} is FAILED or CANCELED. See Sync attempt log: #{}".format(
                    sync_attempt.product_feed.name, sync_attempt.id
                )
                messages.append(msg)
        if messages:
            slack.publish("\n".join(messages), username="product feed", msg_type=slack.MESSAGE_TYPE_WARNING)
