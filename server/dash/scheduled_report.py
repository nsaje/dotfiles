import datetime
import logging
import pytz
import json

from django.conf import settings
from django.db import transaction

from utils import exc

from dash import models
from dash import constants
from dash import export_plus
from dash import forms
from dash.views import helpers

logger = logging.getLogger(__name__)


def get_due_scheduled_reports():
    today = datetime.date.today()
    due_reports = models.ScheduledExportReport.objects.select_related('report').filter(
        state=constants.ScheduledReportState.ACTIVE)

    if today.isoweekday() != 1:  # weekly reports are only sent on Mondays
        due_reports = due_reports.exclude(
            sending_frequency=constants.ScheduledReportSendingFrequency.WEEKLY)

    if today.day != 1:  # montly reports are only sent on the 1st
        due_reports = due_reports.exclude(
            sending_frequency=constants.ScheduledReportSendingFrequency.MONTHLY)

    return due_reports


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


def add_scheduled_report_from_request(request, by_source=False, ad_group=None, campaign=None, account=None):
    try:
        r = json.loads(request.body)
    except ValueError:
        raise exc.ValidationError(message='Invalid json')
    filtered_sources = []
    print r.get('filtered_sources')
    if len(r.get('filtered_sources')) > 0:
        filtered_sources = helpers.get_filtered_sources(request.user, r.get('filtered_sources'))
    add_scheduled_report(
        request.user,
        report_name=r.get('report_name'),
        filtered_sources=filtered_sources,
        order=r.get('order'),
        additional_fields=r.get('additional_fields'),
        granularity=export_plus.get_granularity_from_type(r.get('type')),
        by_day=r.get('by_day') or False,
        by_source=by_source,
        ad_group=ad_group,
        campaign=campaign,
        account=account,
        sending_frequency=get_sending_frequency(r.get('frequency')),
        recipient_emails=r.get('recipient_emails'))


def add_scheduled_report(
        user,
        report_name='',
        filtered_sources=[],
        order=None,
        additional_fields='',
        granularity=constants.ScheduledReportGranularity.CONTENT_AD,
        by_day=False,
        by_source=False,
        ad_group=None,
        campaign=None,
        account=None,
        sending_frequency=constants.ScheduledReportSendingFrequency.DAILY,
        recipient_emails=''):

    if not user.has_perm('zemauth.exports_plus'):
        raise exc.ForbiddenError(message='Not allowed')

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
