import datetime
from mock import patch

from django import test

from dash import models
from dash import constants
from dash import scheduled_report


class ScheduledReportTestCase(test.TestCase):
    fixtures = ['test_api']

    class MockDatetime(object):
        @classmethod
        def today(cls):
            return datetime.datetime(2016, 6, 8)

        @classmethod
        def utcnow(cls):
            return datetime.datetime(2016, 6, 8, 8, 8)

    @patch('dash.scheduled_report.datetime')
    def test_get_due_scheduled_reports(self, datetime_mock):
        datetime_mock.datetime = self.MockDatetime()

        ser = models.ScheduledExportReport.objects.get(id=1)

        self.assertEqual(ser.sending_frequency, constants.ScheduledReportSendingFrequency.DAILY)
        self.assertTrue(ser in scheduled_report.get_due_scheduled_reports())

        ser.sending_frequency = constants.ScheduledReportSendingFrequency.WEEKLY
        ser.save()
        self.assertTrue(datetime_mock.today().isoweekday() != 1)  # Not Monday
        self.assertFalse(ser in scheduled_report.get_due_scheduled_reports())

        ser.sending_frequency = constants.ScheduledReportSendingFrequency.MONTHLY
        ser.save()
        self.assertTrue(datetime_mock.today().day != 1)  # Not First
        self.assertFalse(ser in scheduled_report.get_due_scheduled_reports())

    @patch('dash.scheduled_report.datetime')
    def test_get_scheduled_report_date_range(self, datetime_mock):
        datetime_mock.datetime = self.MockDatetime()
        datetime_mock.timedelta = datetime.timedelta

        self.assertEqual(
            (datetime.date(2016, 6, 7), datetime.date(2016, 6, 7)),
            scheduled_report.get_scheduled_report_date_range(constants.ScheduledReportSendingFrequency.DAILY))

        self.assertEqual(
            (datetime.date(2016, 6, 1), datetime.date(2016, 6, 7)),
            scheduled_report.get_scheduled_report_date_range(constants.ScheduledReportSendingFrequency.WEEKLY))

        self.assertEqual(
            (datetime.date(2016, 5, 8), datetime.date(2016, 6, 7)),
            scheduled_report.get_scheduled_report_date_range(constants.ScheduledReportSendingFrequency.MONTHLY))
