import datetime
from mock import patch

from django.test import TestCase
from mixer.backend.django import mixer

from dash import constants
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
    def test_filter_due(self, now_mock):
        mixer.cycle(3).blend(
            models.ScheduledReport,
            state=(v for v in constants.ScheduledReportState._VALUES),
            query={},
        )
        mixer.cycle(3).blend(
            models.ScheduledReport,
            sending_frequency=(v for v in constants.ScheduledReportSendingFrequency._VALUES),
            last_sent_dt=datetime.datetime(2017, 3, 31, 15),
            query={}
        )
        self.assertEqual(6, models.ScheduledReport.objects.all().count())

        # already sent
        now_mock.return_value = datetime.datetime(2017, 3, 31, 15, 1)
        self.assertEqual(1, models.ScheduledReport.objects.all().filter_due().count())

        # already sent
        now_mock.return_value = datetime.datetime(2017, 3, 31, 23, 59)
        self.assertEqual(1, models.ScheduledReport.objects.all().filter_due().count())

        # monthly and not already sent
        now_mock.return_value = datetime.datetime(2017, 4, 1, 6)
        self.assertEqual(3, models.ScheduledReport.objects.all().filter_due().count())

        # daily only
        now_mock.return_value = datetime.datetime(2017, 4, 2)
        self.assertEqual(2, models.ScheduledReport.objects.all().filter_due().count())

        # weekly
        now_mock.return_value = datetime.datetime(2017, 4, 3)
        self.assertEqual(3, models.ScheduledReport.objects.all().filter_due().count())

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
