import logging
import traceback

from django.core.management.base import BaseCommand

from dash import models
from dash import constants
from dash import scheduled_report

from utils.statsd_helper import statsd_timer
from utils.statsd_helper import statsd_gauge

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    @statsd_timer('dash.scheduled_reports', 'send_scheduled_export_reports_job')
    def handle(self, *args, **options):
        logger.info('Sending Scheduled Export Report Emails')

        due_scheduled_reports = scheduled_report.get_due_scheduled_reports()
        statsd_gauge('dash.scheduled_reports.num_reports_due', len(due_scheduled_reports))
        num_reports_logs_made = num_success_logs = num_failed_logs = 0
        for sr in due_scheduled_reports:
            report = sr.report
            log = models.ScheduledExportReportLog()
            log.scheduled_report = sr
            log.report = report

            try:
                start_date, end_date = scheduled_report.get_scheduled_report_date_range(sr.sending_frequency)
                report_contents, report_filename = scheduled_report.get_scheduled_report(report, start_date, end_date)
                email_adresses = sr.get_recipients_emails_list()

                log.start_date = start_date
                log.end_date = end_date
                log.report_filename = report_filename
                log.recipient_emails = ', '.join(email_adresses)

                scheduled_report.send_scheduled_report(sr.name, email_adresses, report_contents, report_filename)
                log.state = constants.ScheduledReportSent.SUCCESS
                num_success_logs += 1

            except Exception as e:
                logger.warning(e.message, exc_info=(traceback))
                log.add_error(e.message)
                num_failed_logs += 1

            log.save()
            num_reports_logs_made += 1

        statsd_gauge('dash.scheduled_reports.num_reports_logs_made', num_reports_logs_made)
        statsd_gauge('dash.scheduled_reports.num_reports_logs_sucessful', num_success_logs)
        statsd_gauge('dash.scheduled_reports.num_reports_logs_failed', num_failed_logs)
        logger.info('Finished Sending Scheduled Export Report Emails')
