import random
import threading
import time

from django.conf import settings

from dash import constants
from dash import models


class MockAsyncValidation(threading.Thread):
    def __init__(self, candidate, batch_callback, fail_probability=0.0, sleep_time=None, *args, **kwargs):
        assert settings.DEBUG or settings.TESTING
        super(MockAsyncValidation, self).__init__(*args, **kwargs)
        self.candidate = candidate
        self.batch_callback = batch_callback
        self.fail_probability = fail_probability
        self.sleep_time = sleep_time

    def run(self):
        if not self.sleep_time:
            self.sleep_time = random.randint(2, 5)
        time.sleep(self.sleep_time)

        try:
            self.candidate = models.ContentAdCandidate.objects.get(id=self.candidate.id)
        except Exception:
            return

        rand = random.random()
        if self.candidate.image_status != constants.AsyncUploadJobStatus.PENDING_START:
            if rand > self.fail_probability:
                self.candidate.image_id = "p/srv/8678/13f72b5e37a64860a73ac95ff51b2a3e"
                self.candidate.image_hash = "1234"
                self.candidate.image_height = 500
                self.candidate.image_width = 500
                self.candidate.image_status = constants.AsyncUploadJobStatus.OK
            else:
                self.candidate.image_status = constants.AsyncUploadJobStatus.FAILED

        rand = random.random()
        if self.candidate.url_status != constants.AsyncUploadJobStatus.PENDING_START:
            if rand > self.fail_probability:
                self.candidate.url_status = constants.AsyncUploadJobStatus.OK
            else:
                self.candidate.url_status = constants.AsyncUploadJobStatus.FAILED

        self.candidate.save()
        self.batch_callback(self.candidate.batch)
