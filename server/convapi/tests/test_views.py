from django.test import TestCase, RequestFactory

import hmac
import hashlib
import datetime
from convapi import views
from django.conf import settings

class ViewsTest(TestCase):

    def setUp(self):
        # Every test needs access to the request factory.
        self.factory = RequestFactory()

    def _authorize(self):
        timestamp = datetime.datetime.now()
        signature = hmac.new(
            key=settings.MAILGUN_API_KEY,
            msg='{}{}'.format(timestamp, ""),
            digestmod=hashlib.sha256
        ).hexdigest()
        return timestamp, signature

    def test_mailgun_gareps(self):
        # Create an instance of a GET request.
        timestamp, signature = self._authorize()
        request = self.factory.post('/convapi/mailgun/gareps/', {
            'subject': 'test',
            'sender': 'test@zemanta.com',
            'timestamp': timestamp,
            'recipient': 'processor@zemanta.com',
            'from': 'test@zemanta.com',
            'attachment-count': 1,
            'signature': signature,
            'token': '',
            })
        views.mailgun_gareps(request)

        '''
        ga_report_task = tasks.GAReportTask(request.POST.get('subject'),
                                             request.POST.get('Date'),
                                             request.POST.get('sender'),
                                             request.POST.get('recipient'),
                                             request.POST.get('from'),
                                             None,
                                             key,
                                             attachment_name,
                                             request.POST.get('attachment-count', 0),
        '''
