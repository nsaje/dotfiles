import datetime
import logging
import pytz

from django.conf import settings
from django.db import transaction

from utils import exc

from dash import models
from dash import constants
from dash import forms

logger = logging.getLogger(__name__)


def get_due_scheduled_reports():
    today = pytz.UTC.localize(datetime.datetime.utcnow())

    due_reports = models.ScheduledExportReport.objects.select_related('report').filter(
        state=constants.ScheduledReportState.ACTIVE)

    reports_sent_today = models.ScheduledExportReportLog.objects.filter(created_dt__gte=_get_yesterday(today)).all()
    if reports_sent_today.exists():
        due_reports = due_reports.exclude(id__in=[rep.scheduled_report.id for rep in reports_sent_today])

    if today.isoweekday() != 1:  # weekly reports are only sent on Mondays
        due_reports = due_reports.exclude(
            sending_frequency=constants.ScheduledReportSendingFrequency.WEEKLY)

    if today.day != 1:  # montly reports are only sent on the 1st
        due_reports = due_reports.exclude(
            sending_frequency=constants.ScheduledReportSendingFrequency.MONTHLY)

    return due_reports


def _get_yesterday(today):
    return today - datetime.timedelta(days=1, hours=-1)


def get_scheduled_report_date_range(sending_frequency):
    today_utc = pytz.UTC.localize(datetime.datetime.utcnow())
    today = today_utc.astimezone(pytz.timezone(settings.DEFAULT_TIME_ZONE)).replace(tzinfo=None).date()
    yesterday = today - datetime.timedelta(days=1)

    if sending_frequency == constants.ScheduledReportSendingFrequency.DAILY:
        return (yesterday, yesterday)
    elif sending_frequency == constants.ScheduledReportSendingFrequency.WEEKLY:
        week_ago = yesterday - datetime.timedelta(days=6)
        return (week_ago, yesterday)
    elif sending_frequency == constants.ScheduledReportSendingFrequency.MONTHLY:
        if today.month == 1:
            month_ago = today.replace(month=12, year=today.year - 1)
        else:
            month_ago = today.replace(month=today.month - 1)
        return (month_ago, yesterday)
    return None, None


def get_sending_frequency(freq):
    return {
        'daily': constants.ScheduledReportSendingFrequency.DAILY,
        'weekly': constants.ScheduledReportSendingFrequency.WEEKLY,
        'monthly': constants.ScheduledReportSendingFrequency.MONTHLY
    }.get(freq)


def add_scheduled_report(
        user,
        report_name='',
        filtered_sources=[],
        order=None,
        additional_fields='',
        granularity=constants.ScheduledReportGranularity.CONTENT_AD,
        by_day=False,
        by_source=False,
        include_model_ids=False,
        ad_group=None,
        campaign=None,
        account=None,
        sending_frequency=constants.ScheduledReportSendingFrequency.DAILY,
        recipient_emails=''):

    if not user.has_perm('zemauth.can_include_model_ids_in_reports'):
        include_model_ids = False

    form = forms.ScheduleReportForm(
        {
            'report_name': report_name,
            'granularity': granularity,
            'frequency': sending_frequency,
            'recipient_emails': recipient_emails
        })

    if not form.is_valid():
        raise exc.ValidationError(errors=form.errors)

    with transaction.atomic():
        export_report = models.ExportReport(
            created_by=user,
            ad_group=ad_group,
            campaign=campaign,
            account=account,
            granularity=form.cleaned_data['granularity'],
            order_by=order,
            breakdown_by_source=by_source,
            breakdown_by_day=by_day,
            include_model_ids=include_model_ids,
            additional_fields=additional_fields)
        export_report.save()
        for s in filtered_sources:
            export_report.filtered_sources.add(s)

        scheduled_report = models.ScheduledExportReport(
            created_by=user,
            name=form.cleaned_data['report_name'],
            report=export_report,
            sending_frequency=form.cleaned_data['frequency'])
        scheduled_report.save()

        scheduled_report.set_recipient_emails_list(form.cleaned_data['recipient_emails'])
