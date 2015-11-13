import datetime
import logging
import pytz

from django.conf import settings
from django.core.mail.message import EmailMessage

from dash import models
from dash import constants
from dash import export_plus


logger = logging.getLogger(__name__)


def get_due_scheduled_reports():
    today = datetime.date.today()
    due_reports = models.ScheduledExportReport.objects.select_related('report').filter(state=constants.ScheduledReportState.ACTIVE)

    if today.isoweekday() != 1:
        due_reports = due_reports.exclude(sending_frequency=constants.ScheduledReportSendingFrequency.WEEKLY)

    if today.day != 1:
        due_reports = due_reports.exclude(sending_frequency=constants.ScheduledReportSendingFrequency.MONTHLY)

    return due_reports


def get_scheduled_report_date_range(sending_frequency):
    today_utc = pytz.UTC.localize(datetime.datetime.utcnow())
    today = today_utc.astimezone(pytz.timezone(settings.DEFAULT_TIME_ZONE)).replace(tzinfo=None)
    today = datetime.date(today.year, today.month, today.day)
    yesterday = today - datetime.timedelta(days=1)

    if sending_frequency == constants.ScheduledReportSendingFrequency.DAILY:
        return (yesterday, yesterday)
    elif sending_frequency == constants.ScheduledReportSendingFrequency.WEEKLY:
        week_ago = yesterday - datetime.timedelta(days=6)
        return (week_ago, yesterday)
    elif sending_frequency == constants.ScheduledReportSendingFrequency.MONTHLY:
        month_ago = today.replace(month=today.month - 1)
        return (month_ago, yesterday)
    return None


def get_scheduled_report(export_report, start_date, end_date):
    user = export_report.created_by
    filtered_sources = export_report.get_filtered_sources()
    order = export_report.order_by
    additional_fields = export_report.get_additional_fields()
    granularity = export_report.granularity
    breakdown = export_plus.get_breakdown_from_granularity(granularity)
    by_source = export_report.breakdown_by_source
    by_day = export_report.breakdown_by_day
    ad_group = export_report.ad_group
    campaign = export_report.campaign
    account = export_report.account

    contents = _get_scheduled_report_contents(
        user,
        filtered_sources,
        start_date,
        end_date,
        order,
        additional_fields,
        breakdown,
        by_source,
        by_day,
        account_id=(account.id if account else None),
        campaign_id=(campaign.id if campaign else None),
        ad_group_id=(ad_group.id if ad_group else None)
    )

    account_name = campaign_name = ad_group_name = None
    if account:
        account_name = account.name
    elif campaign:
        account_name = campaign.account.name
        campaign_name = campaign.name
    elif ad_group:
        account_name = ad_group.campaign.account.name
        campaign_name = ad_group.campaign.name
        ad_group_name = ad_group.name

    filename = export_plus.get_report_filename(
        granularity,
        start_date,
        end_date,
        account_name=(account_name if account_name else None),
        campaign_name=(campaign_name if campaign_name else None),
        ad_group_name=(ad_group_name if ad_group_name else None),
        by_source=by_source,
        by_day=by_day
    )

    return (contents, filename)


def _get_scheduled_report_contents(user, filtered_sources, start_date, end_date, order, additional_fields, breakdown, by_source, by_day, account_id=None, campaign_id=None, ad_group_id=None):
    arguments = {
        'user': user,
        'filtered_sources': filtered_sources,
        'start_date': start_date,
        'end_date': end_date,
        'order': order,
        'additional_fields': additional_fields,
        'breakdown': breakdown,
        'by_source': by_source,
        'by_day': by_day
    }

    if account_id:
        arguments['account_id'] = account_id
        return export_plus.AccountExport().get_data(**arguments)
    elif campaign_id:
        arguments['campaign_id'] = campaign_id
        return export_plus.CampaignExport().get_data(**arguments)
    elif ad_group_id:
        arguments['ad_group_id'] = ad_group_id
        return export_plus.AdGroupExport().get_data(**arguments)
    return export_plus.AllAccountsExport().get_data(**arguments)


def send_scheduled_report(report_name, email_adresses, report_contents, report_filename):
    subject = u'Zemanta Scheduled Report: {}'.format(
        report_name
    )
    # NOTE: waiting for email copy from product, will replace
    body = u'''Hi,

Please find attached Your scheduled report {report_name}.

Yours truly,
Zemanta
    '''
    body = body.format(
        report_name=report_name
    )
    if not email_adresses:
        raise Exception('No recipient emails: ' + report_name)
    email = EmailMessage(subject, body, 'help@zemanta.com', email_adresses)
    email.attach(report_filename + '.csv', report_contents, 'text/csv')
    email.send(fail_silently=False)
