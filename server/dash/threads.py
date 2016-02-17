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
    def __init__(self, batch_id, *args, **kwargs):
        self.batch_id = batch_id
        self.exception_queue = Queue.Queue()
        self.bump_queue = Queue.Queue()
        super(UpdateUploadBatchThread, self).__init__(*args, **kwargs)

    def check_exception(self):
        try:
            ex = self.exception_queue.get_nowait()
            if ex:
                raise ex
        except Queue.Empty:
            pass

    def bump_propagated(self):
        self.bump_queue.put_nowait('propagated_content_ads')
        self.check_exception()

    def bump_inserted(self):
        self.bump_queue.put_nowait('inserted_content_ads')
        self.check_exception()

    def finish(self):
        self.bump_queue.put_nowait('die')

    def _get_upload_batch_attr(self, attr_name):
        return models.UploadBatch.objects.filter(pk=self.batch_id).values(attr_name)[0].get(attr_name)

    def run(self):
        messages_todo = self._get_upload_batch_attr('batch_size') * 2
        while messages_todo > 0:
            messages_todo -= 1

            message = self.bump_queue.get()

            if self._get_upload_batch_attr('cancelled'):
                self.exception_queue.put_nowait(exceptions.UploadCancelledException())
                break

            if message == 'inserted_content_ads':
                # update atomically
                models.UploadBatch.objects.filter(pk=self.batch_id).update(
                    inserted_content_ads=F('inserted_content_ads') + 1)
            elif message == 'propagated_content_ads':
                models.UploadBatch.objects.filter(pk=self.batch_id).update(
                    propagated_content_ads=F('propagated_content_ads') + 1)
            else:
                # die
                break


class CreateUpdateContentAdsActions(Thread):

    def start(self):
        # block when testing so that results can be verified
        # else do not block
        super(CreateUpdateContentAdsActions, self).start()
        if settings.TESTING:
            self.join()
