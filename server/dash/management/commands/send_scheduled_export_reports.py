import logging

from django.core.management.base import BaseCommand

from dash import models
from dash import constants
from dash import scheduled_report
from dash import export_plus

from utils.command_helpers import ExceptionCommand
from utils.statsd_helper import statsd_timer
from utils.statsd_helper import statsd_gauge
from utils import email_helper

logger = logging.getLogger(__name__)


class Command(ExceptionCommand):
    @statsd_timer('dash.scheduled_reports', 'send_scheduled_export_reports_job')
    def handle(self, *args, **options):
        logger.info('Sending Scheduled Export Report Emails')

        due_scheduled_reports = scheduled_report.get_due_scheduled_reports()
        num_reports_logs_made = num_success_logs = num_failed_logs = 0
        for sr in due_scheduled_reports:
            report_log = models.ScheduledExportReportLog()
            report_log.scheduled_report = sr

            try:
                start_date, end_date = scheduled_report.get_scheduled_report_date_range(sr.sending_frequency)
                email_adresses = sr.get_recipients_emails_list()
                report_log.start_date = start_date
                report_log.end_date = end_date
                report_log.recipient_emails = ', '.join(email_adresses)

                report_contents, report_filename = export_plus.get_report_from_export_report(sr.report, start_date, end_date)
                report_log.report_filename = report_filename

                email_helper.send_scheduled_export_report(
                    report_name=sr.name,
                    frequency=constants.ScheduledReportSendingFrequency.get_text(sr.sending_frequency),
                    granularity=constants.ScheduledReportGranularity.get_text(sr.report.granularity),
                    entity_level=constants.ScheduledReportLevel.get_text(sr.report.level),
                    entity_name=sr.report.get_exported_entity_name(),
                    scheduled_by=sr.created_by.email,
                    email_adresses=email_adresses,
                    report_contents=report_contents,
                    report_filename=report_filename)

                report_log.state = constants.ScheduledReportSent.SUCCESS
                num_success_logs += 1

            except Exception as e:
                logger.exception('Exception raised while sending scheduled export report.')
                report_log.add_error(e.message)
                num_failed_logs += 1

            report_log.save()
            num_reports_logs_made += 1

        statsd_gauge('dash.scheduled_reports.num_reports_due', len(due_scheduled_reports))
        statsd_gauge('dash.scheduled_reports.num_reports_logs_made', num_reports_logs_made)
        statsd_gauge('dash.scheduled_reports.num_reports_logs_sucessful', num_success_logs)
        statsd_gauge('dash.scheduled_reports.num_reports_logs_failed', num_failed_logs)
        logger.info('Finished Sending Scheduled Export Report Emails - OK: %s Fail: %s - Total: %s Expected: %s',
                    num_success_logs, num_failed_logs, num_reports_logs_made, len(due_scheduled_reports))
