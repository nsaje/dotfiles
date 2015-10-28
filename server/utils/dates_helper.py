import pytz
import datetime

def utc_today():
    now = datetime.datetime.utcnow()
    return now.date() 

def est_today():
    now = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)
    return now.astimezone(pytz.timezone('EST')).date()
