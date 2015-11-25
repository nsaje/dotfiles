import datetime
from mock import patch

from django import test

from dash import models
from dash import constants
from dash import scheduled_report


class MockDatetime(datetime.datetime):
    @classmethod
    def today(cls):
        return cls(2016, 6, 8)

    @classmethod
    def utcnow(cls):
        return cls(2016, 6, 8, 8, 8)
datetime.datetime = MockDatetime


class ScheduledReportTestCase(test.TestCase):
    fixtures = ['test_api']

    def test_get_due_scheduled_reports(self):
        ser = models.ScheduledExportReport.objects.get(id=1)

        self.assertEqual(ser.sending_frequency, constants.ScheduledReportSendingFrequency.DAILY)
        self.assertTrue(ser in scheduled_report.get_due_scheduled_reports())

        ser.sending_frequency = constants.ScheduledReportSendingFrequency.WEEKLY
        ser.save()
        self.assertTrue(datetime.datetime.today().isoweekday() != 1)  # Not Monday
        self.assertFalse(ser in scheduled_report.get_due_scheduled_reports())

        ser.sending_frequency = constants.ScheduledReportSendingFrequency.MONTHLY
        ser.save()
        self.assertTrue(datetime.datetime.today().day != 1)  # Not First
        self.assertFalse(ser in scheduled_report.get_due_scheduled_reports())

    def test_get_scheduled_report_date_range(self):
        self.assertEqual(
            (datetime.date(2016, 6, 7), datetime.date(2016, 6, 7)),
            scheduled_report.get_scheduled_report_date_range(constants.ScheduledReportSendingFrequency.DAILY))

        self.assertEqual(
            (datetime.date(2016, 6, 1), datetime.date(2016, 6, 7)),
            scheduled_report.get_scheduled_report_date_range(constants.ScheduledReportSendingFrequency.WEEKLY))

        self.assertEqual(
            (datetime.date(2016, 5, 8), datetime.date(2016, 6, 7)),
            scheduled_report.get_scheduled_report_date_range(constants.ScheduledReportSendingFrequency.MONTHLY))
