import datetime
import logging
import pytz

from django.conf import settings
from django.db import transaction
from django.db.models import Q

from utils import exc
from utils import email_helper

from dash import models
from dash import constants
from dash import forms
from dash import export

logger = logging.getLogger(__name__)


def get_due_scheduled_reports():
    today = pytz.UTC.localize(datetime.datetime.utcnow())

    due_reports = models.ScheduledExportReport.objects.select_related('report').filter(
        state=constants.ScheduledReportState.ACTIVE)

    reports_sent_today = models.ScheduledExportReportLog.objects.filter(created_dt__gte=_get_yesterday(today)).all()
    if reports_sent_today.exists():
        due_reports = due_reports.exclude(id__in=[rep.scheduled_report.id for rep in reports_sent_today])

    due_reports = due_reports.exclude(
        ~Q(day_of_week=today.isoweekday()),
        sending_frequency=constants.ScheduledReportSendingFrequency.WEEKLY,
    )

    if today.day != 1:  # montly reports are only sent on the 1st
        due_reports = due_reports.exclude(
            sending_frequency=constants.ScheduledReportSendingFrequency.MONTHLY)

    return due_reports


def send_scheduled_report(scheduled_report):
    report_log = models.ScheduledExportReportLog()
    report_log.scheduled_report = scheduled_report

    try:
        start_date, end_date = get_scheduled_report_date_range(scheduled_report.time_period)
        email_adresses = scheduled_report.get_recipients_emails_list()
        report_log.start_date = start_date
        report_log.end_date = end_date
        report_log.recipient_emails = ', '.join(email_adresses)

        report_contents, report_filename = export.get_report_from_export_report(
            scheduled_report.report, start_date, end_date)
        report_log.report_filename = report_filename

        email_helper.send_scheduled_export_report(
            report_name=scheduled_report.name,
            frequency=constants.ScheduledReportSendingFrequency.get_text(scheduled_report.sending_frequency),
            granularity=constants.ScheduledReportGranularity.get_text(scheduled_report.report.granularity),
            entity_level=constants.ScheduledReportLevel.get_text(scheduled_report.report.level),
            entity_name=scheduled_report.report.get_exported_entity_name(),
            scheduled_by=scheduled_report.created_by.email,
            email_adresses=email_adresses,
            report_contents=report_contents,
            report_filename=report_filename)

        report_log.state = constants.ScheduledReportSent.SUCCESS

    except Exception as e:
        logger.exception('Exception raised while sending scheduled export report.')
        report_log.add_error(e.message)

    report_log.save()
    return report_log


def _get_yesterday(today):
    return today - datetime.timedelta(days=1, hours=-1)


def get_scheduled_report_date_range(time_period):
    today_utc = pytz.UTC.localize(datetime.datetime.utcnow())
    today = today_utc.astimezone(pytz.timezone(settings.DEFAULT_TIME_ZONE)).replace(tzinfo=None).date()
    yesterday = today - datetime.timedelta(days=1)

    if time_period == constants.ScheduledReportTimePeriod.YESTERDAY:
        return (yesterday, yesterday)
    elif time_period == constants.ScheduledReportTimePeriod.LAST_7_DAYS:
        before_7_days = today - datetime.timedelta(days=7)
        return (before_7_days, yesterday)
    elif time_period == constants.ScheduledReportTimePeriod.LAST_30_DAYS:
        before_30_days = today - datetime.timedelta(days=30)
        return (before_30_days, yesterday)
    elif time_period == constants.ScheduledReportTimePeriod.THIS_WEEK:
        if today.isoweekday() != 7:
            sunday = today - datetime.timedelta(days=today.isoweekday())
        else:
            sunday = today
        return (sunday, yesterday)
    elif time_period == constants.ScheduledReportTimePeriod.LAST_WEEK:
        if today.isoweekday() != 7:
            last_saturday = today - datetime.timedelta(days=today.isoweekday() + 1)
        else:
            last_saturday = today - datetime.timedelta(days=1)
        last_sunday = last_saturday - datetime.timedelta(days=6)
        return (last_sunday, last_saturday)
    elif time_period == constants.ScheduledReportTimePeriod.THIS_MONTH:
        first = today - datetime.timedelta(days=today.day - 1)
        return (first, yesterday)
    elif time_period == constants.ScheduledReportTimePeriod.LAST_MONTH:
        last = today - datetime.timedelta(days=today.day)
        first = last - datetime.timedelta(days=last.day - 1)
        return (first, last)
    return None, None


def get_sending_frequency(freq):
    return {
        'daily': constants.ScheduledReportSendingFrequency.DAILY,
        'weekly': constants.ScheduledReportSendingFrequency.WEEKLY,
        'monthly': constants.ScheduledReportSendingFrequency.MONTHLY
    }.get(freq)


def _get_default_time_period(sending_frequency):
    return {
        constants.ScheduledReportSendingFrequency.DAILY: constants.ScheduledReportTimePeriod.YESTERDAY,
        constants.ScheduledReportSendingFrequency.WEEKLY: constants.ScheduledReportTimePeriod.LAST_WEEK,
        constants.ScheduledReportSendingFrequency.MONTHLY: constants.ScheduledReportTimePeriod.LAST_MONTH,
    }.get(sending_frequency)


def add_scheduled_report(
        user,
        report_name='',
        filtered_sources=[],
        filtered_agencies=[],
        filtered_account_types=[],
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
        day_of_week=constants.ScheduledReportDayOfWeek.MONDAY,
        time_period=constants.ScheduledReportTimePeriod.YESTERDAY,
        recipient_emails=''):

    if not user.has_perm('zemauth.can_include_model_ids_in_reports'):
        include_model_ids = False

    if not user.has_perm('zemauth.can_set_time_period_in_scheduled_reports'):
        time_period = _get_default_time_period(sending_frequency)

    if not user.has_perm('zemauth.can_set_day_of_week_in_scheduled_reports'):
        day_of_week = constants.ScheduledReportDayOfWeek.MONDAY

    form = forms.ScheduleReportForm(
        {
            'report_name': report_name,
            'granularity': granularity,
            'frequency': sending_frequency,
            'day_of_week': day_of_week,
            'time_period': time_period,
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
            additional_fields=additional_fields,
            filtered_account_types=filtered_account_types
        )
        export_report.save()
        for s in filtered_sources:
            export_report.filtered_sources.add(s)
        if filtered_agencies:
            for agency in filtered_agencies:
                export_report.filtered_agencies.add(agency)

        scheduled_report = models.ScheduledExportReport(
            created_by=user,
            name=form.cleaned_data['report_name'],
            report=export_report,
            sending_frequency=form.cleaned_data['frequency'],
            day_of_week=form.cleaned_data['day_of_week'],
            time_period=form.cleaned_data['time_period'],
        )
        scheduled_report.save()

        scheduled_report.set_recipient_emails_list(form.cleaned_data['recipient_emails'])
