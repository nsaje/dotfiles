#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.test import TestCase, RequestFactory

import hmac
import hashlib
import datetime
import StringIO
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

    def test_mailgun_gareps_no_attachment(self):
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

    def test_mailgun_gareps(self):
        f = StringIO.StringIO()
        f.write("""
# ----------------------------------------
# All Web Site Data
# Landing Pages
# 20150416-20150416
# ----------------------------------------

Landing Page,Device Category,Sessions,% New Sessions,New Users,Bounce Rate,Pages/Session,Avg. Session Duration,Yell Free Listings (Goal 1 Conversion Rate),Yell Free Listings (Goal 1 Completions),Yell Free Listings (Goal 1 Value)
/lasko?_z1_adgid=1&_z1_msid=lasko,mobile,553,96.02%,531,92.41%,1.12,00:00:12,0.00%,0,£0.00
,,"3,215",95.43%,"3,068",88.99%,1.18,00:00:17,0.00%,0,£0.00

Day Index,Sessions
16/04/2015,"553"
,"553"
        """.strip())
        # Create an instance of a GET request.
        timestamp, signature = self._authorize()
        request = self.factory.post('/convapi/mailgun/gareps/', {
            'Date': 'Tue, 21 Apr 2015 17:20:35 +0200',
            'subject': 'test',
            'sender': 'test@zemanta.com',
            'timestamp': timestamp,
            'recipient': 'processor@zemanta.com',
            'from': 'test@zemanta.com',
            'attachment-count': 1,
            'signature': signature,
            'token': '',
            })
        f.name = "test"
        request.FILES['attachment-1'] = f
        response = views.mailgun_gareps(request)
        self.assertEqual(response.status_code, 200)
