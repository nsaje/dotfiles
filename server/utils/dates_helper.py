import pytz
import datetime

from django.conf import settings


def local_to_utc_time(dt):
    tz = pytz.timezone(settings.DEFAULT_TIME_ZONE)
    dt = tz.localize(dt)
    return dt.astimezone(pytz.utc)


def utc_datetime_to_local_date(dt):
    dt = dt.replace(tzinfo=pytz.utc)
    return dt.astimezone(pytz.timezone(settings.DEFAULT_TIME_ZONE)).date()


def utc_today():
    now = datetime.datetime.utcnow()
    return now.date()


def local_today():
    return utc_datetime_to_local_date(datetime.datetime.utcnow())
