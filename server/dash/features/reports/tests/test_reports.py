import datetime
import mock

from celery.exceptions import SoftTimeLimitExceeded
from django.test import TestCase

from dash.features.reports import constants
from dash.features.reports import models
from dash.features.reports import reports


class ReportsExecuteTest(TestCase):
    def setUp(self):
        self.reportJob = models.ReportJob(status=constants.ReportJobStatus.IN_PROGRESS)
        self.reportJob.save()

    @mock.patch('dash.features.reports.reports.ReportJobExecutor.get_raw_new_report')
    def test_handle_exception(self, mock_get_report):
        mock_get_report.side_effect = Exception('test-error')

        reports.execute(self.reportJob.id)

        mock_get_report.assert_called_once_with(self.reportJob)

        self.reportJob.refresh_from_db()
        self.assertEqual(constants.ReportJobStatus.FAILED, self.reportJob.status)
        self.assertEqual('test-error', self.reportJob.result)

    @mock.patch('dash.features.reports.reports.ReportJobExecutor.get_raw_new_report')
    def test_handle_soft_time_limit(self, mock_get_report):
        mock_get_report.side_effect = SoftTimeLimitExceeded()

        reports.execute(self.reportJob.id)

        mock_get_report.assert_called_once_with(self.reportJob)

        self.reportJob.refresh_from_db()
        self.assertEqual(constants.ReportJobStatus.FAILED, self.reportJob.status)
        self.assertEqual('Timeout', self.reportJob.result)

    @mock.patch('utils.dates_helper.utc_now')
    @mock.patch('dash.features.reports.reports.ReportJobExecutor.get_raw_new_report')
    def test_too_old(self, mock_get_report, mock_now):
        mock_get_report.side_effect = Exception('test-error')
        mock_now.return_value = datetime.datetime(2017, 8, 1, 11, 31)

        self.reportJob.created_dt = datetime.datetime(2017, 8, 1, 10, 30)
        self.reportJob.save()

        reports.execute(self.reportJob.id)

        mock_get_report.assert_not_called()

        self.reportJob.refresh_from_db()
        self.assertEqual(constants.ReportJobStatus.FAILED, self.reportJob.status)
        self.assertEqual('Too old', self.reportJob.result)

    @mock.patch('dash.features.reports.reports.ReportJobExecutor.get_raw_new_report')
    def test_incorrect_state(self, mock_get_report):
        mock_get_report.side_effect = Exception('test-error')

        self.reportJob.status = constants.ReportJobStatus.DONE
        self.reportJob.save()

        reports.execute(self.reportJob.id)

        mock_get_report.assert_not_called()
