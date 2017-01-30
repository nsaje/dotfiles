import pytz
import datetime

from django.conf import settings


# NOTE: this function can be mocked in tests to also change the return value
# of every other function in this module that uses current time
def utc_now():
    return datetime.datetime.utcnow()


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
    return utc_now().date()


def local_now():
    return utc_to_local_datetime(utc_now())


def local_today():
    return utc_to_local_datetime(utc_now()).date()


def local_yesterday():
    return local_today() - datetime.timedelta(days=1)


def local_midnight_to_utc_time():
    local_now = utc_to_local_datetime(utc_now())
    local_midnight = local_now.replace(hour=0, minute=0, second=0, microsecond=0)
    return local_midnight.astimezone(pytz.utc)


def count_months(start_date, end_date):
    return (end_date.year - start_date.year) * 12 + end_date.month - start_date.month


def get_overlap(start_date1, end_date1, start_date2, end_date2):
    if start_date1 > end_date2 or start_date2 > end_date1:
        return None, None
    return max(start_date1, start_date2), min(end_date1, end_date2)


def date_range(start_date, end_date):
    for n in range(int((end_date - start_date).days)):
        yield start_date + datetime.timedelta(n)


def format_date_mmddyyyy(date):
    return '%d/%d/%d' % (date.month, date.day, date.year)
