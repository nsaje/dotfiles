import datetime
import mock
from mock import patch

from django import test

from dash import models
from dash import constants
from dash import scheduled_report

import zemauth.models


class ScheduledReportTestCase(test.TestCase):
    fixtures = ['test_api']

    class MockDatetime(object):
        @classmethod
        def today(cls):
            return datetime.datetime(2016, 6, 8)

        @classmethod
        def utcnow(cls):
            return datetime.datetime(2016, 6, 8, 8, 8)

    def mock_yesterday(today):
        return today - datetime.timedelta(days=1, hours=-1)

    @patch('dash.scheduled_report.datetime')
    @mock.patch("dash.scheduled_report._get_yesterday", mock_yesterday)
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

        def test_add_scheduled_report(self):
            user = zemauth.models.User.objects.get(pk=2)
            camp = models.Campaign.objects.get(pk=1)
            scheduled_report.add_scheduled_report(
                user,
                report_name='rep',
                filtered_sources=models.Source.objects.get(pk=1),
                order='name',
                additional_fields='cost,impressions',
                granularity=constants.ScheduledReportGranularity.AD_GROUP,
                by_day=False,
                by_source=False,
                ad_group=None,
                campaign=camp,
                account=None,
                sending_frequency=constants.ScheduledReportSendingFrequency.WEEKLY,
                recipient_emails='test@zem.com')

            self.assertEqual(len(models.ExportReport.objects.filter(created_by=user)), 1)
            er = models.ExportReport.objects.filter(created_by=user)[0]
            self.assertEqual(er.ad_group, None)
            self.assertEqual(er.campaign, camp)
            self.assertEqual(er.account, None)
            self.assertEqual(er.granularity, constants.ScheduledReportGranularity.AD_GROUP)
            self.assertFalse(er.breakdown_by_day)
            self.assertFalse(er.breakdown_by_source)
            self.assertEqual(er.order_by, 'name')
            self.assertEqual(er.additional_fields, 'cost,impressions')

            self.assertEqual(len(models.ScheduledExportReport.objects.filter(report_name='rep')), 1)
            ser = models.ScheduledExportReport.objects.filter('report_name')[0]
            self.assertEqual(ser.report, er)
            self.assertEqual(ser.created_by, user)
            self.assertEqual(ser.state, constants.ScheduledReportState.ACTIVE)
            self.assertEqual(ser.sending_frequency, constants.ScheduledReportSendingFrequency.WEEKLY)
            self.assertEqual(ser.get_recipients_emails_list(), ['test@zem.com'])
