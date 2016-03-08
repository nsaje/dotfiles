import pytz
import datetime

from django.conf import settings


def local_to_utc_time(dt):
    tz = pytz.timezone(settings.DEFAULT_TIME_ZONE)
    dt = tz.localize(dt)
    return dt.astimezone(pytz.utc)


def utc_to_tz_datetime(dt, tz):
    dt = dt.replace(tzinfo=pytz.utc)
    return dt.astimezone(tz)


def utc_to_local_datetime(dt):
    return utc_to_tz_datetime(dt, pytz.timezone(settings.DEFAULT_TIME_ZONE))


def utc_datetime_to_local_date(dt):
    return utc_to_local_datetime(dt).date()


def utc_today():
    now = datetime.datetime.utcnow()
    return now.date()


def local_today():
    return utc_to_local_datetime(datetime.datetime.utcnow()).date()


def count_months(start_date, end_date):
    return (end_date.year - start_date.year) * 12 + end_date.month - start_date.month


def get_overlap(start_date1, end_date1, start_date2, end_date2):
    if start_date1 > end_date2 or start_date2 > end_date1:
        return None, None
    return max(start_date1, start_date2), min(end_date1, end_date2)
