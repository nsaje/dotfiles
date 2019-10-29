import core.common
from integrations.product_feeds import exceptions

from . import model


class SyncAttemptManager(core.common.BaseManager):
    def create(self, product_feed, **kwargs):
        if not product_feed:
            raise exceptions.SyncAttemptCreateError("Sync Attempt cannot exists without product feed.")

        batches = kwargs.pop("batches", [])
        ads_paused_and_archived = kwargs.pop("ads_paused_and_archived", [])
        sync_attempt = model.SyncAttempt(product_feed=product_feed, **kwargs)
        sync_attempt.save()
        sync_attempt.batches.add(*batches)
        sync_attempt.ads_paused_and_archived.add(*ads_paused_and_archived)
        return sync_attempt
