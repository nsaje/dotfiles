import datetime
import mock

from celery.exceptions import SoftTimeLimitExceeded
from django.test import TestCase

import core.entity

from dash.features import scheduled_reports
from utils.magic_mixer import magic_mixer

from . import constants
from . import reports
from .reportjob import ReportJob


class ReportsExecuteTest(TestCase):
    def setUp(self):
        self.reportJob = ReportJob(status=constants.ReportJobStatus.IN_PROGRESS)
        self.reportJob.user = magic_mixer.blend_user()
        self.reportJob.save()

        influx_incr_patcher = mock.patch('influx.incr')
        self.mock_influx_incr = influx_incr_patcher.start()
        self.addCleanup(influx_incr_patcher.stop)

    def assertJobFailed(self, status, result, exception=None):
        self.mock_influx_incr.assert_called_once_with('dash.reports', 1, status=status)

        self.reportJob.refresh_from_db()
        self.assertEqual(constants.ReportJobStatus.FAILED, self.reportJob.status)
        self.assertEqual(result, self.reportJob.result)
        if exception is not None:
            self.assertIn(str(exception), self.reportJob.exception)

    @mock.patch('dash.features.reports.reports.ReportJobExecutor._send_fail')
    @mock.patch('dash.features.reports.reports.ReportJobExecutor.get_report')
    def test_handle_exception(self, mock_get_report, mock_send_fail):
        e = Exception('test-error')
        mock_get_report.side_effect = e

        reports.execute(self.reportJob.id)

        mock_get_report.assert_called_once_with(self.reportJob)
        mock_send_fail.assert_called_once_with()
        self.assertJobFailed('failed', 'Internal Error: Please contact support. Report job ID is %d.' % self.reportJob.id, e)

    @mock.patch('dash.features.reports.reports.ReportJobExecutor._send_fail')
    @mock.patch('dash.features.reports.reports.ReportJobExecutor.get_report')
    def test_handle_soft_time_limit(self, mock_get_report, mock_send_fail):
        e = SoftTimeLimitExceeded()
        mock_get_report.side_effect = e

        reports.execute(self.reportJob.id)

        mock_get_report.assert_called_once_with(self.reportJob)
        mock_send_fail.assert_called_once_with()
        self.assertJobFailed('timeout', 'Job Timeout: Requested report probably too large. Report job ID is %d.' % self.reportJob.id)

    @mock.patch('utils.dates_helper.utc_now')
    @mock.patch('dash.features.reports.reports.ReportJobExecutor._send_fail')
    @mock.patch('dash.features.reports.reports.ReportJobExecutor.get_report')
    def test_too_old(self, mock_get_report, mock_send_fail, mock_now):
        mock_get_report.side_effect = Exception('test-error')
        mock_now.return_value = datetime.datetime(2017, 8, 1, 11, 31)

        self.reportJob.created_dt = datetime.datetime(2017, 8, 1, 10, 30)
        self.reportJob.save()

        reports.execute(self.reportJob.id)

        mock_get_report.assert_not_called()
        mock_send_fail.assert_called_once_with()
        self.assertJobFailed('too_old', 'Service Timeout: Please try again later.')

    @mock.patch('dash.features.reports.reports.ReportJobExecutor.get_report')
    def test_incorrect_state(self, mock_get_report):
        mock_get_report.side_effect = Exception('test-error')

        self.reportJob.status = constants.ReportJobStatus.DONE
        self.reportJob.save()

        reports.execute(self.reportJob.id)

        mock_get_report.assert_not_called()

    @mock.patch('utils.email_helper.send_async_report_fail')
    def test_send_fail(self, mock_send):
        ad_group = magic_mixer.blend(core.entity.AdGroup, campaign__account__users=[self.reportJob.user])
        self.reportJob.query = {
            'options': {
                'recipients': ['test@test.com'],
                'show_archived': False,
                'show_blacklisted_publishers': False,
                'include_totals': False,
            },
            'filters': [
                {'field': 'Date', 'operator': 'between', 'from': '2017-08-01', 'to': '2017-08-01'},
                {'field': 'Ad Group Id', 'operator': '=', 'value': str(ad_group.id)},
            ],
            'fields': [{'field': 'Content Ad'}, {'field': 'Clicks'}],
        }

        executor = reports.ReportJobExecutor(self.reportJob)
        executor._send_fail()

        mock_send.assert_called_once_with(
            user=self.reportJob.user,
            recipients=['test@test.com'],
            start_date=datetime.date(2017, 8, 1),
            end_date=datetime.date(2017, 8, 1),
            filtered_sources=[],
            show_archived=False,
            show_blacklisted_publishers=False,
            view='Content Ad',
            breakdowns=[],
            columns=['Content Ad', 'Clicks'],
            include_totals=False,
            ad_group_name=ad_group.name,
            campaign_name=ad_group.campaign.name,
            account_name=ad_group.campaign.account.name,
        )

    @mock.patch('utils.email_helper.send_async_report_fail')
    def test_send_fail_scheduled_report(self, mock_send):
        self.reportJob.query = {
            'options': {
                'recipients': ['test@test.com'],
            },
        }
        self.reportJob.scheduled_report = scheduled_reports.models.ScheduledReport()

        executor = reports.ReportJobExecutor(self.reportJob)
        executor._send_fail()

        mock_send.assert_not_called()

    @mock.patch('dash.features.reports.reports.ReportJobExecutor.send_by_email')
    @mock.patch('dash.features.reports.reports.ReportJobExecutor.save_to_s3')
    @mock.patch('dash.features.reports.reports.ReportJobExecutor.get_report')
    def test_success(self, mock_get_report, mock_save, mock_send):
        mock_get_report.return_value = (1, 2)
        mock_save.return_value = 'test-report-path'

        reports.execute(self.reportJob.id)

        self.mock_influx_incr.assert_called_once_with('dash.reports', 1, status='success')

        self.reportJob.refresh_from_db()
        self.assertEqual(constants.ReportJobStatus.DONE, self.reportJob.status)
        self.assertEqual('test-report-path', self.reportJob.result)
