import datetime

from django.test import TestCase
from mock import patch

from dash import constants

from . import helpers


class GetScheduledReportDateRangeTestCase(TestCase):
    @patch("dash.features.scheduled_reports.helpers.datetime")
    def test_get_scheduled_report_date_range(self, datetime_mock):
        datetime_mock.datetime.utcnow.return_value = datetime.datetime(2016, 6, 8, 8, 8)
        datetime_mock.timedelta = datetime.timedelta

        self.assertEqual(
            (datetime.date(2016, 6, 7), datetime.date(2016, 6, 7)),
            helpers.get_scheduled_report_date_range(constants.ScheduledReportTimePeriod.YESTERDAY),
        )
        self.assertEqual(
            (datetime.date(2016, 6, 1), datetime.date(2016, 6, 7)),
            helpers.get_scheduled_report_date_range(constants.ScheduledReportTimePeriod.LAST_7_DAYS),
        )
        self.assertEqual(
            (datetime.date(2016, 5, 9), datetime.date(2016, 6, 7)),
            helpers.get_scheduled_report_date_range(constants.ScheduledReportTimePeriod.LAST_30_DAYS),
        )

    @patch("dash.features.scheduled_reports.helpers.datetime")
    def test_get_scheduled_report_date_range_sunday(self, datetime_mock):
        datetime_mock.datetime.utcnow.return_value = datetime.datetime(2016, 8, 14, 8, 8)
        datetime_mock.timedelta = datetime.timedelta
        self.assertEqual(
            (datetime.date(2016, 8, 14), datetime.date(2016, 8, 13)),
            helpers.get_scheduled_report_date_range(constants.ScheduledReportTimePeriod.THIS_WEEK),
        )
        self.assertEqual(
            (datetime.date(2016, 8, 7), datetime.date(2016, 8, 13)),
            helpers.get_scheduled_report_date_range(constants.ScheduledReportTimePeriod.LAST_WEEK),
        )

    @patch("dash.features.scheduled_reports.helpers.datetime")
    def test_get_scheduled_report_date_range_saturday(self, datetime_mock):
        datetime_mock.datetime.utcnow.return_value = datetime.datetime(2016, 8, 13, 8, 8)
        datetime_mock.timedelta = datetime.timedelta
        self.assertEqual(
            (datetime.date(2016, 8, 7), datetime.date(2016, 8, 12)),
            helpers.get_scheduled_report_date_range(constants.ScheduledReportTimePeriod.THIS_WEEK),
        )
        self.assertEqual(
            (datetime.date(2016, 7, 31), datetime.date(2016, 8, 6)),
            helpers.get_scheduled_report_date_range(constants.ScheduledReportTimePeriod.LAST_WEEK),
        )

    @patch("dash.features.scheduled_reports.helpers.datetime")
    def test_get_scheduled_report_date_range_monday(self, datetime_mock):
        datetime_mock.datetime.utcnow.return_value = datetime.datetime(2016, 8, 15, 8, 8)
        datetime_mock.timedelta = datetime.timedelta
        self.assertEqual(
            (datetime.date(2016, 8, 14), datetime.date(2016, 8, 14)),
            helpers.get_scheduled_report_date_range(constants.ScheduledReportTimePeriod.THIS_WEEK),
        )
        self.assertEqual(
            (datetime.date(2016, 8, 7), datetime.date(2016, 8, 13)),
            helpers.get_scheduled_report_date_range(constants.ScheduledReportTimePeriod.LAST_WEEK),
        )

    @patch("dash.features.scheduled_reports.helpers.datetime")
    def test_get_scheduled_report_date_range_first(self, datetime_mock):
        datetime_mock.datetime.utcnow.return_value = datetime.datetime(2016, 8, 1, 8, 8)
        datetime_mock.timedelta = datetime.timedelta
        self.assertEqual(
            (datetime.date(2016, 8, 1), datetime.date(2016, 7, 31)),
            helpers.get_scheduled_report_date_range(constants.ScheduledReportTimePeriod.THIS_MONTH),
        )
        self.assertEqual(
            (datetime.date(2016, 7, 1), datetime.date(2016, 7, 31)),
            helpers.get_scheduled_report_date_range(constants.ScheduledReportTimePeriod.LAST_MONTH),
        )

    @patch("dash.features.scheduled_reports.helpers.datetime")
    def test_get_scheduled_report_date_range_last(self, datetime_mock):
        datetime_mock.datetime.utcnow.return_value = datetime.datetime(2016, 8, 31, 8, 8)
        datetime_mock.timedelta = datetime.timedelta
        self.assertEqual(
            (datetime.date(2016, 8, 1), datetime.date(2016, 8, 30)),
            helpers.get_scheduled_report_date_range(constants.ScheduledReportTimePeriod.THIS_MONTH),
        )
        self.assertEqual(
            (datetime.date(2016, 7, 1), datetime.date(2016, 7, 31)),
            helpers.get_scheduled_report_date_range(constants.ScheduledReportTimePeriod.LAST_MONTH),
        )
