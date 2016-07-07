from threading import Thread
import logging

from django.conf import settings

logger = logging.getLogger(__name__)

TRANSACTION_END_WAIT = 3


class CreateUpdateContentAdsActions(Thread):

    def start(self):
        # block when testing so that results can be verified
        # else do not block
        super(CreateUpdateContentAdsActions, self).start()
        if settings.TESTING:
            self.join()
