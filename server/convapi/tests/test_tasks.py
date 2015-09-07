#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.test import TestCase

import dash
import xlsxwriter
import StringIO

from convapi import tasks
from convapi import models
from convapi import views


class TasksTest(TestCase):

    fixtures = ['test_ga_aggregation.yaml']

    def _fake_get_ga_from_s3(self, key):
        return """
# ----------------------------------------
# All Web Site Data
# Landing Pages
# 20150416-20150416
# ----------------------------------------

Landing Page,Device Category,Sessions,% New Sessions,New Users,Bounce Rate,Pages/Session,Avg. Session Duration,Yell Free Listings (Goal 1 Conversion Rate),Yell Free Listings (Goal 1 Completions),Yell Free Listings (Goal 1 Value)
/lasko?_z1_caid=1000&_z1_adgid=1&_z1_msid=adblade,mobile,553,96.02%,531,92.41%,1.12,00:00:12,0.00%,0,£0.00,,"3,215",95.43%,"3,068",88.99%,1.18,00:00:17,0.00%,0,£0.00

Day Index,Sessions
16/04/2015,"553"
,"553"
        """.strip()

    def test_process_ga_report(self):
        dash.models.Source.objects.create(source_type=None, name='Test source', tracking_slug='lasko', maintenance=False)

        tasks.get_from_s3 = self._fake_get_ga_from_s3
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

    def test_process_ga_report_v2(self):
        dash.models.Source.objects.create(source_type=None, name='Test source', tracking_slug='lasko', maintenance=False)

        tasks.get_from_s3 = self._fake_get_ga_from_s3
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
        tasks.process_ga_report_v2(ga_report_task)

        report_logs = models.GAReportLog.objects.all()[0]
        self.assertIsNone(report_logs.errors)

    def _fake_get_omniture_from_s3(self, key):
        csv_omniture_report = """
,,,,,,,,,,
AdobeÂ® Scheduled Report,,,,,,,,,,
Report Suite: Global,,,,,,,,,,
Date: Sun. 19 Apr. 2015,,,,,,,,,,
Segment: All Visits (No Segment),,,,,,,,,,
,,,,,,,,,,
Report Type: Ranked,,,,,,,,,,
"Selected Metrics: Visits, Unique Visitors, Bounce Rate, Page Views, Total Seconds Spent",,,,,,,,,,
Broken Down by: None,,,,,,,,,,
Data Filter: CSY-PB-ZM-AB,,,,,,,,,,
Compare to Report Suite: None,,,,,,,,,,
Compare to Segment: None,,,,,,,,,,
Item Filter: None,,,,,,,,,,
Percent Shown as: Number,,,,,,,,,,
,,,,,,,,,,
,,,,,,,,,,
,Tracking Code,Visits,,Unique Visitors,,Bounce Rate,Page Views,,Total Seconds Spent,
1.,CSY-PB-ZM-AB-adbistro_com:Fad-or-Fab-4-Unusual-New-Car-Features,1,0.0%,1,0.0%,100.0%,1,0.0%,0,0.0%
2.,CSY-PB-ZM-AB-infolinks_com:Fires-and-Other-Home-Hazards-Spike-During-the-Holidays-Data-Show,1,0.0%,1,0.0%,
3.,CSY-PB-ZM-AB-adbistro_com:Bikers-Born-to-Be-Wild-VIDEO,1,0.0%,1,0.0%,100.0%,1,0.0%,0,0.0%
4.,CSY-PB-ZM-AB-yahoo_com:7-Useful-Items-for-Your-Glove-Compartment,1,0.0%,1,0.0%,100.0%,1,0.0%,0,0.0%
,Total,"2,227",,"2,184",,88.6%,"2,670",,"63,745",
    """.strip().decode('utf-8')
        # Create a workbook and add a worksheet.
        buf = StringIO.StringIO()
        workbook = xlsxwriter.Workbook(buf)
        worksheet = workbook.add_worksheet()
        lines = (line.split(',') for line in csv_omniture_report.split('\n'))
        # Iterate over the data and write it out row by row.
        for row, line in enumerate(lines):
            for col, el in enumerate(line):
                worksheet.write(row, col, el)
        workbook.close()
        return buf.getvalue()

    def test_process_omniture_report(self):
        dash.models.Source.objects.create(source_type=None, name='Test source', tracking_slug='lasko', maintenance=False)

        tasks.get_from_s3 = self._fake_get_omniture_from_s3
        report_task = views.GAReportTask('GA mail',
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
        tasks.process_omniture_report(report_task)

        report_logs = models.GAReportLog.objects.all()[0]
        # TODO: Finish test
        # self.assertIsNone(report_logs.errors)
