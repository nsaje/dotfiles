import pytz
import datetime

from django.conf import settings

def utc_today():
    now = datetime.datetime.utcnow()
    return now.date()

def local_today():
    now = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)
    return now.astimezone(pytz.timezone(settings.DEFAULT_TIME_ZONE)).date()
