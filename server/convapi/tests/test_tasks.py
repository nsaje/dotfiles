#!/usr/bin/env python
# -*- coding: utf-8 -*-

from mock import patch
from django.test import TestCase

import dash

from convapi import tasks
from convapi import models
from convapi import views
from utils import csv_utils

from reports import redshift


@patch('reports.redshift.get_cursor')
class TasksTest(TestCase):
    fixtures = ['test_ga_aggregation.yaml']

    def setUp(self):
        redshift.STATS_DB_NAME = 'default'

    def _fake_get_ga_day_index_from_s3(self, key):
        return """
# ----------------------------------------
# All Web Site Data
# Landing Pages
# 20150416-20150416
# ----------------------------------------

Landing Page,Device Category,Sessions,% New Sessions,New Users,Bounce Rate,Pages/Session,Avg. Session Duration,Yell Free Listings (Goal 1 Conversion Rate),Yell Free Listings (Goal 1 Completions),Yell Free Listings (Goal 1 Value)
/lasko?_z1_caid=1&_z1_adgid=1&_z1_msid=yahoo,mobile,553,96.02%,531,92.41%,1.12,00:00:12,0.00%,0,£0.00,,"3,215",95.43%,"3,068",88.99%,1.18,00:00:17,0.00%,0,£0.00

Day Index,Sessions
16/04/2015,"553"
,"553"
        """.strip()

    def _fake_get_ga_hour_index_from_s3(self, key):
        return """
# ----------------------------------------
# All Web Site Data
# Landing Pages
# 20150416-20150416
# ----------------------------------------

Landing Page,Device Category,Sessions,% New Sessions,New Users,Bounce Rate,Pages/Session,Avg. Session Duration,Yell Free Listings (Goal 1 Conversion Rate),Yell Free Listings (Goal 1 Completions),Yell Free Listings (Goal 1 Value)
/lasko?_z1_caid=1&_z1_adgid=1&_z1_msid=yahoo,mobile,553,96.02%,531,92.41%,1.12,00:00:12,0.00%,0,£0.00,,"3,215",95.43%,"3,068",88.99%,1.18,00:00:17,0.00%,0,£0.00

Hour Index,Sessions
0,1
1,1
2,1
3,1
4,1
5,1
6,1
7,1
8,1
9,1
10,1
11,1
12,1
13,1
14,1
15,1
16,1
17,1
18,1
19,1
20,1
21,1
22,1
23,530
,"553"
        """.strip()

    def _fake_get_omni_from_s3(self, key):
        with open('convapi/fixtures/omniture_tracking_codes_modified.xls', 'rb') as f:
            return f.read()

    def _fake_get_omni_zip_from_s3(self, key):
        with open('convapi/fixtures/omniture_tracking_codes_xls.zip', 'rb') as f:
            return f.read()

    def _fake_get_omni_csv_zip_from_s3(self, key):
        with open('convapi/fixtures/omniture_tracking_codes_csv.zip', 'rb') as f:
            return f.read()

    def test_process_ga_report(self, cursor):
        dash.models.Source.objects.create(source_type=None, name='Test source', tracking_slug='lasko', maintenance=False)

        tasks.get_from_s3 = self._fake_get_ga_day_index_from_s3
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

        report_logs = models.GAReportLog.objects.first()
        self.assertIsNone(report_logs.errors)

    def test_process_ga_report_hour_index(self, cursor):
        dash.models.Source.objects.create(source_type=None, name='Test source', tracking_slug='lasko', maintenance=False)

        tasks.get_from_s3 = self._fake_get_ga_hour_index_from_s3
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

        report_logs = models.GAReportLog.objects.first()
        self.assertIsNone(report_logs.errors)

    def test_omni_ga_conversion(self, cursor):
        tasks.get_from_s3 = self._fake_get_omni_from_s3
        ga_report_task = views.GAReportTask('GA mail',
            '2015-07-12',
            'testuser@zemanta.com',
            'mailbot@zemanta.com',
            'testuser@zemanta.com',
            None,
            'lasko',
            'omniture_tracking_codes.xls',
            1,
            'text/csv',
        )
        tasks.process_ga_report(ga_report_task)

        report_log = models.GAReportLog.objects.first()
        self.assertFalse(report_log.errors is None)
        self.assertEqual(234, report_log.visits_reported)
        self.assertEqual(234, report_log.visits_imported)

    def test_process_ga_report_v2(self, cursor):
        dash.models.Source.objects.create(source_type=None, name='Test source', tracking_slug='lasko', maintenance=False)

        tasks.get_from_s3 = self._fake_get_ga_day_index_from_s3
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

        report_log = models.ReportLog.objects.first()
        self.assertIsNone(report_log.errors)

        self.assertEqual(553, report_log.visits_reported)
        self.assertEqual(553, report_log.visits_imported)

    def test_process_ga_report_hour_index_v2(self, cursor):
        tasks.get_from_s3 = self._fake_get_ga_hour_index_from_s3
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

        report_log = models.ReportLog.objects.first()
        self.assertIsNone(report_log.errors)

        self.assertEqual(553, report_log.visits_reported)
        self.assertEqual(553, report_log.visits_imported)

    def test_process_ga_report_v2_omni(self, cursor):
        tasks.get_from_s3 = self._fake_get_omni_from_s3
        ga_report_task = views.GAReportTask('GA mail',
            '2015-07-12',
            'testuser@zemanta.com',
            'mailbot@zemanta.com',
            'testuser@zemanta.com',
            None,
            'lasko',
            'omniture_tracking_codes.xls',
            1,
            'text/csv',
        )
        tasks.process_omniture_report_v2(ga_report_task)

        report_log = models.ReportLog.objects.first()
        self.assertIsNone(report_log.errors)
        self.assertEqual(234, report_log.visits_reported)
        self.assertEqual(234, report_log.visits_imported)

    def test_process_ga_report_v2_omni_zip(self, cursor):
        tasks.get_from_s3 = self._fake_get_omni_zip_from_s3
        ga_report_task = views.GAReportTask('GA mail',
            '2015-07-12',
            'testuser@zemanta.com',
            'mailbot@zemanta.com',
            'testuser@zemanta.com',
            None,
            'lasko',
            'omniture_tracking_codes.zip',
            1,
            'text/csv',
        )
        tasks.process_omniture_report_v2(ga_report_task)

        report_log = models.ReportLog.objects.first()
        self.assertIsNone(report_log.errors)
        self.assertEqual(234, report_log.visits_reported)
        self.assertEqual(234, report_log.visits_imported)

    def test_process_ga_report_v2_omni_csv_zip(self, cursor):
        tasks.get_from_s3 = self._fake_get_omni_csv_zip_from_s3  # self._fake_get_omni_zip_from_s3
        ga_report_task = views.GAReportTask('GA mail',
            '2015-07-12',
            'testuser@zemanta.com',
            'mailbot@zemanta.com',
            'testuser@zemanta.com',
            None,
            'lasko',
            'omniture_tracking_codes.zip',
            1,
            'text/csv',
        )
        tasks.process_omniture_report_v2(ga_report_task)

        report_log = models.ReportLog.objects.first()
        self.assertFalse(report_log.errors is None)
        self.assertEqual(0, report_log.visits_reported)
        self.assertEqual(4112, report_log.visits_imported)

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
1.,CSY-PB-ZM-AB-adbistro_com-z11yahoo1z:Fad-or-Fab-4-Unusual-New-Car-Features,1,0.0%,1,0.0%,100.0%,1,0.0%,100,0.0%
2.,CSY-PB-ZM-AB-infolinks_com-z12yahoo1z:Fires-and-Other-Home-Hazards-Spike-During-the-Holidays-Data-Show,1,0.0%,1,0.0%,100.0%,1,0.0%,0,0.0%
3.,CSY-PB-ZM-AB-adbistro_com--z13yahoo1z:Bikers-Born-to-Be-Wild-VIDEO,1,0.0%,1,0.0%,100.0%,1,0.0%,0,0.0%
4.,CSY-PB-ZM-AB-yahoo_com-z14yahoo1z:7-Useful-Items-for-Your-Glove-Compartment,1,0.0%,1,0.0%,100.0%,1,0.0%,0,0.0%
,Total,4,,4,,88.6%,"2,670",,100,
    """.strip().decode('utf-8')
        return csv_utils.convert_to_xls(csv_omniture_report)

    def test_process_omniture_report(self, cursor):
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

        report_log = models.GAReportLog.objects.first()
        self.assertIsNone(report_log.errors)
