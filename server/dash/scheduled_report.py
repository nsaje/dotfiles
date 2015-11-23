import datetime
import logging
import pytz

from django.conf import settings

from dash import models
from dash import constants

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
    today = today_utc.astimezone(pytz.timezone(settings.DEFAULT_TIME_ZONE)).replace(tzinfo=None)
    today = datetime.date(today.year, today.month, today.day)
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
