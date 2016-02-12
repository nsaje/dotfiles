from threading import Thread
import logging
import Queue

from django.conf import settings
from django.db.models import F

from dash import models
from dash import exceptions
import actionlog.zwei_actions

logger = logging.getLogger(__name__)


class SendActionLogsThread(Thread):
    '''
    This is a hack used to escape transaction that wraps every django admin method.
    It's not intended to be used elsewhere.
    '''
    def __init__(self, action_logs, *args, **kwargs):
        self.action_logs = action_logs
        super(SendActionLogsThread, self).__init__(*args, **kwargs)

    def run(self):
        actionlog.zwei_actions.send(self.action_logs)


class UpdateUploadBatchThread(Thread):
    def __init__(self, batch_id, bump_inserted=False, bump_propagated=False, *args, **kwargs):
        self.batch_id = batch_id
        self.exception_queue = Queue.Queue()
        self.bump_inserted = bump_inserted
        self.bump_propagated = bump_propagated
        super(UpdateUploadBatchThread, self).__init__(*args, **kwargs)

    def start_and_join(self):
        # hack around the fact that all db tests are ran in transaction
        # not calling parent constructor causes run to be called as a normal
        # function
        if settings.TESTING:
            self.run()
            return
        self.start()
        self.join()

        try:
            ex = self.exception_queue.get_nowait()
            if ex:
                raise ex
        except Queue.Empty:
            pass

    def run(self):
        batch = models.UploadBatch.objects.get(pk=self.batch_id)
        if self.bump_inserted:
            batch.inserted_content_ads = F('inserted_content_ads') + 1
        if self.bump_propagated:
            batch.propagated_content_ads = F('propagated_content_ads') + 1
        if batch.cancelled:
            self.exception_queue.put_nowait(exceptions.UploadCancelledException())
        batch.save()


class CreateUpdateContentAdsActions(Thread):

    def start(self):
        # block when testing so that results can be verified
        # else do not block
        super(CreateUpdateContentAdsActions, self).start()
        if settings.TESTING:
            self.join()
