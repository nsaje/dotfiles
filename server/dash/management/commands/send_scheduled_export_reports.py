import datetime
import logging

from django.core.management.base import BaseCommand

from dash import models
from dash import constants
import zemauth

from utils import statsd_helper

logger = logging.getLogger(__name__)


class Command(BaseCommand):

    def handle(self, *args, **options):
        logger.info('Sending Scheduled Export Report Emails')
        '''
        u = zemauth.models.User.objects.get(id=349)
        adg = dash.models.AdGroup.objects.get(id=705)
        new_scheduled_report = dash.models.ScheduledReport(
            name='First Scheduled Report',
            created_by=u, order_by='-source',
            ad_group=adg,
            breakdown_by_source=True)
        new_scheduled_report.save()

        new_scheduled_report.filtered_sources.add(dash.models.Source.objects.get(id=3))
        new_scheduled_report.filtered_sources.add(dash.models.Source.objects.get(id=4))

        new_scheduled_report.add_recipient_email('sdadsadsad@gmail.com')
        new_scheduled_report.add_recipient_email('sadsadsadsad@gmail.com')
        new_scheduled_report.add_recipient_email('sadsadsadsadsadsad@gmail.com')
        new_scheduled_report.set_recipient_emails_list(['d@gmail.com', 'sss@gmail.com', 'wooo@gmail.com'])
        new_scheduled_report.add_recipient_email('aaaaa@gmail.com')
        new_scheduled_report.add_recipient_email('aaaaa@gmail.com')
        new_scheduled_report.add_recipient_email('aaaaa@gmail.com')
        new_scheduled_report.add_recipient_email('aaaaa@gmail.com')
        new_scheduled_report.recipients.create(email='bbbbb@gmail.com')
        new_scheduled_report.recipients.create(email='nn@gmail.com')
        new_scheduled_report.remove_recipient_email('baaabbbb@gmail.com')

        print 'aa', new_scheduled_report.get_recipients_emails_list()
        print 'bb', new_scheduled_report.level
        print 'cc', new_scheduled_report.filtered_sources.all()
        '''
        for scheduled_report in _get_due_scheduled_reports():

            start_date, end_date = _get_scheduled_report_date_range(scheduled_report.sending_frequency)
            report_contents = _get_scheduled_report_contents(scheduled_report.report, start_date, end_date)
            report_filename = _get_scheduled_report_filename(scheduled_report.report, start_date, end_date)
            email_adresses = scheduled_report.get_recipients_emails_list()
            _send_scheduled_report(email_adresses, report_contents, report_filename)

    def _get_due_scheduled_reports():
        today = datetime.date.today()
        due_reports = models.ScheduledExportReport.objects.select_related('report').filter(state=constants.ScheduledReportState.ACTIVE)

        if today.isoweekday() != 1:
            due_reports = due_reports.exclude(sending_frequency=constants.ScheduledReportSendingFrequency.WEEKLY)

        if today.day != 1:
            due_reports = due_reports.exclude(sending_frequency=constants.ScheduledReportSendingFrequency.MONTHLY)

        return due_reports

    def _get_scheduled_report_date_range(sending_frequency):
        today_utc = pytz.UTC.localize(datetime.datetime.utcnow())
        today = today_utc.astimezone(pytz.timezone(settings.DEFAULT_TIME_ZONE)).replace(tzinfo=None)
        today = datetime.datetime(today.year, today.month, today.day)
        yesterday = today - datetime.timedelta(days=1)

        if sending_frequency == constants.ScheduledReportSendingFrequency.DAILY:
            return (yesterday, yesterday)
        elif sending_frequency == constants.ScheduledReportSendingFrequency.WEEKLY:
            week_ago = yesterday - datetime.timedelta(days=1)
            return (week_ago, yesterday)
        elif sending_frequency == constants.ScheduledReportSendingFrequency.MONTHLY:
            first_of_last_month = yesterday - datetime.timedelta(days=1)
            return (week_ago, yesterday)
        return None

    def _get_scheduled_report_filename(export_report, start_date, end_date):
        return ''

    def _get_scheduled_report_contents(export_report, start_date, end_date):
        level = export_report.level
        user = export_report.created_by
        filtered_sources = export_report.filtered_sources.all()
        order = export_report.order
        additional_fields = export_report.additional_fields
        breakdown = export_plus.get_breakdown_from_granularity(export_report.granularity)
        by_source = export_report.breakdown_by_source

        #TODO: Ce to dela, potem zbrisi zgoraj spremenljivke ker niso potrebne

        arguments = {
            'filtered_sources': filtered_sources,
            'start_date': start_date,
            'end_date': end_date,
            'order': order,
            'additional_fields': additional_fields,
            'breakdown': breakdown,
            'by_source': by_source
        }

        if level == constants.ScheduledReportLevel.ALL_ACCOUNTS:
            return export_plus.AllAccountsExport().get_data(
                user,
                **arguments)
        elif level == constants.ScheduledReportLevel.ACCOUNT:
            return export_plus.AccountExport().get_data(
                user,
                export_report.account.id,
                **arguments)
        elif level == constants.ScheduledReportLevel.CAMPAIGN:
            return export_plus.CampaignExport().get_data(
                user,
                export_report.campaign.id,
                **arguments)
        elif level == constants.ScheduledReportLevel.AD_GROUP:
            return export_plus.AdGroupExport().get_data(
                user,
                **arguments)


    def _send_scheduled_report(email_adresses, report_contents, report_filename):
        # Dejansko poslje email z priponko
