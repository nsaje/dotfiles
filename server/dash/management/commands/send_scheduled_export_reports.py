import logging

import influx

from dash import constants
from dash import scheduled_report
from utils.command_helpers import ExceptionCommand

logger = logging.getLogger(__name__)


class Command(ExceptionCommand):
    @influx.timer('dash.scheduled_reports.send_scheduled_export_reports_job')
    def handle(self, *args, **options):
        logger.info('Sending Scheduled Export Report Emails')

        due_scheduled_reports = scheduled_report.get_due_scheduled_reports()
        num_reports_logs_made = num_success_logs = num_failed_logs = 0
        for sr in due_scheduled_reports:
            report_log = scheduled_report.send_scheduled_report(sr)
            if report_log.state == constants.ScheduledReportSent.SUCCESS:
                num_success_logs += 1
            elif report_log.state == constants.ScheduledReportSent.FAILED:
                num_failed_logs += 1
            num_reports_logs_made += 1

        influx.gauge('dash.scheduled_reposts.num_reports.total', len(due_scheduled_reports), type='due')
        influx.gauge('dash.scheduled_reposts.num_reports.total', num_reports_logs_made, type='logs_made')

        influx.gauge('dash.scheduled_reports.num_reports.status', num_success_logs, status='success')
        influx.gauge('dash.scheduled_reports.num_reports.status', num_failed_logs, status='failed')

        logger.info('Finished Sending Scheduled Export Report Emails - OK: %s Fail: %s - Total: %s Expected: %s',
                    num_success_logs, num_failed_logs, num_reports_logs_made, len(due_scheduled_reports))
