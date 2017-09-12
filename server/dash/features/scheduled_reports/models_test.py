import datetime
from mock import patch

from django.test import TestCase
from mixer.backend.django import mixer

from dash import constants
from dash.features import reports
from dash.features.scheduled_reports import models


class ScheduledReportTestCase(TestCase):
    def test_get_recipients(self):
        recipients = ['recipient1', 'recipient2']
        query = {
            'options': {
                'recipients': recipients,
            }
        }
        report = models.ScheduledReport(
            query=query,
        )

        self.assertEqual(recipients, report.get_recipients())

    @patch('utils.dates_helper.utc_now')
    def test_filter_due_status(self, now_mock):
        scheduled_reports = mixer.cycle(4).blend(
            models.ScheduledReport,
            sending_frequency=constants.ScheduledReportSendingFrequency.DAILY,
            query={},
        )
        mixer.cycle(4).blend(
            reports.ReportJob,
            scheduled_report=(v for v in scheduled_reports),
            status=(v for v in reports.constants.ReportJobStatus._VALUES),
            query={},
        )
        reports.ReportJob.objects.all().update(
            created_dt=datetime.datetime(2017, 3, 31, 15),
        )
        self.assertEqual(4, models.ScheduledReport.objects.all().count())

        # already sent, retry only FAILED
        now_mock.return_value = datetime.datetime(2017, 3, 31, 15, 1)
        self.assertEqual(1, models.ScheduledReport.objects.all().filter_due().count())

        # already sent, retry only FAILED
        now_mock.return_value = datetime.datetime(2017, 3, 31, 23, 59)
        self.assertEqual(1, models.ScheduledReport.objects.all().filter_due().count())

        # not sent yet
        now_mock.return_value = datetime.datetime(2017, 4, 1, 6)
        self.assertEqual(4, models.ScheduledReport.objects.all().filter_due().count())

    def test_filter_due_state(self):
        mixer.cycle(2).blend(
            models.ScheduledReport,
            sending_frequency=constants.ScheduledReportSendingFrequency.DAILY,
            state=(v for v in constants.ScheduledReportState._VALUES),
            query={},
        )
        self.assertEqual(2, models.ScheduledReport.objects.all().count())

        self.assertEqual(1, models.ScheduledReport.objects.all().filter_due().count())

    @patch('utils.dates_helper.utc_now')
    def test_filter_due_frequency(self, now_mock):
        mixer.cycle(3).blend(
            models.ScheduledReport,
            sending_frequency=(v for v in constants.ScheduledReportSendingFrequency._VALUES),
            query={},
        )
        self.assertEqual(3, models.ScheduledReport.objects.all().count())

        # daily and monthly
        now_mock.return_value = datetime.datetime(2017, 4, 1, 6)
        self.assertEqual(2, models.ScheduledReport.objects.all().filter_due().count())

        # daily
        now_mock.return_value = datetime.datetime(2017, 4, 2)
        self.assertEqual(1, models.ScheduledReport.objects.all().filter_due().count())

        # daily and weekly
        now_mock.return_value = datetime.datetime(2017, 4, 3)
        self.assertEqual(2, models.ScheduledReport.objects.all().filter_due().count())

    def test_set_date_filter(self):
        query = {
            'filters': [
                {
                    'field': 'Ad Group Id',
                    'operator': '=',
                    'value': '2040'
                },
                {
                    'field': 'Date',
                    'operator': 'between',
                    'from': '2016-10-01',
                    'to': '2016-10-31'
                },
            ]
        }

        report = models.ScheduledReport(query=query)

        start_date = datetime.datetime(2017, 4, 10)
        end_date = datetime.datetime(2017, 4, 11)

        report.set_date_filter(start_date, end_date)

        self.assertEqual(report.query['filters'][1]['from'], start_date)
        self.assertEqual(report.query['filters'][1]['to'], end_date)
