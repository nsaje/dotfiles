import datetime

import mock

import dash.features.scheduled_reports.models
from utils import dates_helper
from utils.base_test_case import BaseTestCase
from utils.magic_mixer import magic_mixer
from utils.test_helper import disable_auto_now_add

from . import ReportJob
from . import constants
from . import helpers


class HelpersTestCase(BaseTestCase):
    @mock.patch("prodops.helpers.reprocess_report_jobs_async")
    def test_reprocess_report_jobs_for_today(self, mock_reprocess_report_jobs_async):
        with disable_auto_now_add(ReportJob, "created_dt"):
            magic_mixer.cycle(10).blend(
                ReportJob,
                scheduled_report=(magic_mixer.blend(dash.features.scheduled_reports.models.ScheduledReport)),
                created_dt=(dates_helper.local_now() - datetime.timedelta(2)),
                status=constants.ReportJobStatus.DONE,
            )
            report_jobs = magic_mixer.cycle(10).blend(
                ReportJob,
                scheduled_report=(magic_mixer.blend(dash.features.scheduled_reports.models.ScheduledReport)),
                created_dt=dates_helper.local_now(),
                status=constants.ReportJobStatus.DONE,
            )

        self.assertTrue(all(r.status == constants.ReportJobStatus.DONE for r in report_jobs))

        helpers.reprocess_report_jobs_for_today()
        for job in report_jobs:
            job.refresh_from_db()

        self.assertTrue(all(j.status == constants.ReportJobStatus.FAILED for j in report_jobs))
        mock_reprocess_report_jobs_async.assert_called_once_with(
            [j.id for j in report_jobs], helpers.REPROCESS_TITLE_PREFIX, helpers.REPROCESS_REASON
        )
