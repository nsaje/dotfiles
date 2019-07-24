import logging

from dash import models
from dash.features import scheduled_reports
from dash.features.reports import reports
from utils import metrics_compat
from utils.command_helpers import Z1Command

logger = logging.getLogger(__name__)


class Command(Z1Command):
    @metrics_compat.timer("dash.scheduled_reports.send_scheduled_reports_job")
    def handle(self, *args, **options):
        logger.info("Sending Scheduled Reports")

        due_scheduled_reports = models.ScheduledReport.objects.all().filter_due()
        for sr in due_scheduled_reports:
            start_date, end_date = scheduled_reports.get_scheduled_report_date_range(sr.time_period)
            sr.set_date_filter(start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))
            reports.create_job(sr.user, sr.query, scheduled_report=sr)
