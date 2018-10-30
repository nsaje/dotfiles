import datetime

import pytz
from django.conf import settings

from dash import constants


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
