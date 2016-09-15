import datetime
import mock
from mock import patch

from django import test
from django.contrib.auth.models import Permission

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
        datetime_mock.datetime.utcnow.return_value = datetime.datetime(2016, 6, 8, 8, 8)
        datetime_mock.timedelta = datetime.timedelta

        self.assertEqual(
            (datetime.date(2016, 6, 7), datetime.date(2016, 6, 7)),
            scheduled_report.get_scheduled_report_date_range(constants.ScheduledReportTimePeriod.YESTERDAY),
        )
        self.assertEqual(
            (datetime.date(2016, 6, 1), datetime.date(2016, 6, 7)),
            scheduled_report.get_scheduled_report_date_range(constants.ScheduledReportTimePeriod.LAST_7_DAYS),
        )
        self.assertEqual(
            (datetime.date(2016, 5, 9), datetime.date(2016, 6, 7)),
            scheduled_report.get_scheduled_report_date_range(constants.ScheduledReportTimePeriod.LAST_30_DAYS),
        )

    @patch('dash.scheduled_report.datetime')
    def test_get_scheduled_report_date_range_sunday(self, datetime_mock):
        datetime_mock.datetime.utcnow.return_value = datetime.datetime(2016, 8, 14, 8, 8)
        datetime_mock.timedelta = datetime.timedelta
        self.assertEqual(
            (datetime.date(2016, 8, 14), datetime.date(2016, 8, 13)),
            scheduled_report.get_scheduled_report_date_range(constants.ScheduledReportTimePeriod.THIS_WEEK),
        )
        self.assertEqual(
            (datetime.date(2016, 8, 7), datetime.date(2016, 8, 13)),
            scheduled_report.get_scheduled_report_date_range(constants.ScheduledReportTimePeriod.LAST_WEEK),
        )

    @patch('dash.scheduled_report.datetime')
    def test_get_scheduled_report_date_range_saturday(self, datetime_mock):
        datetime_mock.datetime.utcnow.return_value = datetime.datetime(2016, 8, 13, 8, 8)
        datetime_mock.timedelta = datetime.timedelta
        self.assertEqual(
            (datetime.date(2016, 8, 7), datetime.date(2016, 8, 12)),
            scheduled_report.get_scheduled_report_date_range(constants.ScheduledReportTimePeriod.THIS_WEEK),
        )
        self.assertEqual(
            (datetime.date(2016, 7, 31), datetime.date(2016, 8, 6)),
            scheduled_report.get_scheduled_report_date_range(constants.ScheduledReportTimePeriod.LAST_WEEK),
        )

    @patch('dash.scheduled_report.datetime')
    def test_get_scheduled_report_date_range_monday(self, datetime_mock):
        datetime_mock.datetime.utcnow.return_value = datetime.datetime(2016, 8, 15, 8, 8)
        datetime_mock.timedelta = datetime.timedelta
        self.assertEqual(
            (datetime.date(2016, 8, 14), datetime.date(2016, 8, 14)),
            scheduled_report.get_scheduled_report_date_range(constants.ScheduledReportTimePeriod.THIS_WEEK),
        )
        self.assertEqual(
            (datetime.date(2016, 8, 7), datetime.date(2016, 8, 13)),
            scheduled_report.get_scheduled_report_date_range(constants.ScheduledReportTimePeriod.LAST_WEEK),
        )

    @patch('dash.scheduled_report.datetime')
    def test_get_scheduled_report_date_range_first(self, datetime_mock):
        datetime_mock.datetime.utcnow.return_value = datetime.datetime(2016, 8, 1, 8, 8)
        datetime_mock.timedelta = datetime.timedelta
        self.assertEqual(
            (datetime.date(2016, 8, 1), datetime.date(2016, 7, 31)),
            scheduled_report.get_scheduled_report_date_range(constants.ScheduledReportTimePeriod.THIS_MONTH),
        )
        self.assertEqual(
            (datetime.date(2016, 7, 1), datetime.date(2016, 7, 31)),
            scheduled_report.get_scheduled_report_date_range(constants.ScheduledReportTimePeriod.LAST_MONTH),
        )

    @patch('dash.scheduled_report.datetime')
    def test_get_scheduled_report_date_range_last(self, datetime_mock):
        datetime_mock.datetime.utcnow.return_value = datetime.datetime(2016, 8, 31, 8, 8)
        datetime_mock.timedelta = datetime.timedelta
        self.assertEqual(
            (datetime.date(2016, 8, 1), datetime.date(2016, 8, 30)),
            scheduled_report.get_scheduled_report_date_range(constants.ScheduledReportTimePeriod.THIS_MONTH),
        )
        self.assertEqual(
            (datetime.date(2016, 7, 1), datetime.date(2016, 7, 31)),
            scheduled_report.get_scheduled_report_date_range(constants.ScheduledReportTimePeriod.LAST_MONTH),
        )

    def test_get_default_time_period(self):
        self.assertEqual(
            constants.ScheduledReportTimePeriod.YESTERDAY,
            scheduled_report._get_default_time_period(constants.ScheduledReportSendingFrequency.DAILY),
        )
        self.assertEqual(
            constants.ScheduledReportTimePeriod.LAST_WEEK,
            scheduled_report._get_default_time_period(constants.ScheduledReportSendingFrequency.WEEKLY),
        )
        self.assertEqual(
            constants.ScheduledReportTimePeriod.LAST_MONTH,
            scheduled_report._get_default_time_period(constants.ScheduledReportSendingFrequency.MONTHLY),
        )

    def test_add_scheduled_report(self):
        user = zemauth.models.User.objects.get(pk=2)
        camp = models.Campaign.objects.get(pk=1)
        scheduled_report.add_scheduled_report(
            user,
            report_name='rep',
            filtered_sources=models.Source.objects.all().filter(pk=1),
            order='name',
            additional_fields='cost,impressions',
            granularity=constants.ScheduledReportGranularity.AD_GROUP,
            by_day=False,
            by_source=False,
            ad_group=None,
            campaign=camp,
            account=None,
            sending_frequency=constants.ScheduledReportSendingFrequency.WEEKLY,
            recipient_emails='test@zem.com',
            time_period=constants.ScheduledReportTimePeriod.YESTERDAY,
        )

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

        self.assertEqual(len(models.ScheduledExportReport.objects.filter(name='rep')), 1)
        ser = models.ScheduledExportReport.objects.filter(name='rep')[0]
        self.assertEqual(ser.report, er)
        self.assertEqual(ser.created_by, user)
        self.assertEqual(ser.state, constants.ScheduledReportState.ACTIVE)
        self.assertEqual(ser.sending_frequency, constants.ScheduledReportSendingFrequency.WEEKLY)
        self.assertEqual(ser.time_period, constants.ScheduledReportTimePeriod.LAST_WEEK)
        self.assertEqual(ser.get_recipients_emails_list(), ['test@zem.com'])

    def test_add_scheduled_report_time_period(self):
        user = zemauth.models.User.objects.get(pk=2)
        permission = Permission.objects.get(codename='can_set_time_period_in_scheduled_reports')
        user.user_permissions.add(permission)
        camp = models.Campaign.objects.get(pk=1)
        scheduled_report.add_scheduled_report(
            user,
            report_name='rep',
            filtered_sources=models.Source.objects.all().filter(pk=1),
            order='name',
            additional_fields='cost,impressions',
            granularity=constants.ScheduledReportGranularity.AD_GROUP,
            by_day=False,
            by_source=False,
            ad_group=None,
            campaign=camp,
            account=None,
            sending_frequency=constants.ScheduledReportSendingFrequency.WEEKLY,
            recipient_emails='test@zem.com',
            time_period=constants.ScheduledReportTimePeriod.YESTERDAY,
        )

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

        self.assertEqual(len(models.ScheduledExportReport.objects.filter(name='rep')), 1)
        ser = models.ScheduledExportReport.objects.filter(name='rep')[0]
        self.assertEqual(ser.report, er)
        self.assertEqual(ser.created_by, user)
        self.assertEqual(ser.state, constants.ScheduledReportState.ACTIVE)
        self.assertEqual(ser.sending_frequency, constants.ScheduledReportSendingFrequency.WEEKLY)
        self.assertEqual(ser.time_period, constants.ScheduledReportTimePeriod.YESTERDAY)
        self.assertEqual(ser.get_recipients_emails_list(), ['test@zem.com'])

    def test_add_scheduled_report_totals(self):
        user = zemauth.models.User.objects.get(pk=2)
        permission = Permission.objects.get(codename='can_include_totals_in_reports')
        user.user_permissions.add(permission)
        camp = models.Campaign.objects.get(pk=1)
        scheduled_report.add_scheduled_report(
            user,
            report_name='rep',
            filtered_sources=models.Source.objects.all().filter(pk=1),
            order='name',
            additional_fields='cost,impressions',
            granularity=constants.ScheduledReportGranularity.AD_GROUP,
            by_day=False,
            by_source=False,
            ad_group=None,
            campaign=camp,
            account=None,
            sending_frequency=constants.ScheduledReportSendingFrequency.WEEKLY,
            recipient_emails='test@zem.com',
            include_totals=True,
        )

        self.assertEqual(len(models.ExportReport.objects.filter(created_by=user)), 1)
        er = models.ExportReport.objects.filter(created_by=user)[0]
        self.assertEqual(er.include_totals, True)

    def test_add_scheduled_report_totals_no_permission(self):
        user = zemauth.models.User.objects.get(pk=2)
        camp = models.Campaign.objects.get(pk=1)
        scheduled_report.add_scheduled_report(
            user,
            report_name='rep',
            filtered_sources=models.Source.objects.all().filter(pk=1),
            order='name',
            additional_fields='cost,impressions',
            granularity=constants.ScheduledReportGranularity.AD_GROUP,
            by_day=False,
            by_source=False,
            ad_group=None,
            campaign=camp,
            account=None,
            sending_frequency=constants.ScheduledReportSendingFrequency.WEEKLY,
            recipient_emails='test@zem.com',
            include_totals=True,
        )

        self.assertEqual(len(models.ExportReport.objects.filter(created_by=user)), 1)
        er = models.ExportReport.objects.filter(created_by=user)[0]
        self.assertEqual(er.include_totals, False)
