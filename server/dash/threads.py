from threading import Thread
import logging

from django.conf import settings

from dash import models
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
    def __init__(self, batch_id, inserted_content_ads, *args, **kwargs):
        self.batch_id = batch_id
        self.inserted_content_ads = inserted_content_ads
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

    def run(self):
        batch = models.UploadBatch.objects.get(pk=self.batch_id)
        batch.inserted_content_ads = self.inserted_content_ads
        batch.save()
