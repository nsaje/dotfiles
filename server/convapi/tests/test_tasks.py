#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.test import TestCase

import dash
import datetime

from convapi import tasks
from convapi import models
from convapi import helpers
from convapi import views


class TasksTest(TestCase):

    fixtures = ['test_ga_aggregation.yaml']

    def _fake_get_from_s3(self, key):
        return """
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
        """.strip()

    def test_process_ga_report(self):
        s = dash.models.Source.objects.create(source_type=None, name='Test source', tracking_slug='lasko', maintenance=False)

        tasks.get_from_s3 = self._fake_get_from_s3
        ga_report_task = views.GAReportTask('GA mail',
            '2015-01-01',
            'testuser@zemanta.com',
            'mailbot@zemanta.com',
            'testuser@zemanta.com',
            None,
            'lasko',
            'Analytics All Web Site Data Landing Pages 20150406-20150406.csv',
            1,
            'text/csv',
        )
        tasks.process_ga_report(ga_report_task)

        report_logs = models.GAReportLog.objects.all()[0]
        self.assertIsNone(report_logs.errors)


    def test_helpers(self):
        self.assertIsNotNone(helpers._generate_s3_report_key(datetime.date.today(), "test", ""))
