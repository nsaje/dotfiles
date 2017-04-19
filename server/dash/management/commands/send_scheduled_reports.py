import datetime
import logging

import influx

from dash import models
from dash import scheduled_report
from dash.features.reports import reports
from utils.command_helpers import ExceptionCommand

logger = logging.getLogger(__name__)


class Command(ExceptionCommand):
    @influx.timer('dash.scheduled_reports.send_scheduled_reports_job')
    def handle(self, *args, **options):
        logger.info('Sending Scheduled Reports')

        due_scheduled_reports = models.ScheduledReport.objects.all().filter_due()
        for sr in due_scheduled_reports:
            start_date, end_date = scheduled_report.get_scheduled_report_date_range(sr.time_period)
            sr.set_date_filter(start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
            reports.create_job(sr.user, sr.query, scheduled_report=sr)

        due_scheduled_reports.update(last_sent_dt=datetime.datetime.now())
