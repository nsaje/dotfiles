import datetime
import re

import boto3
import pytz

from integrations.bizwire import config
from integrations.bizwire import models
from utils import dates_helper

REGEX_KEY_PARTS = re.compile(
    r".*/(?P<year>\d+)/(?P<month>\d+)/(?P<day>\d+)/"
    r"(?P<hour>\d+)(?::|%3[aA])(?P<minute>\d+)/(?P<news_item_id>\d+)r.\.xml"
)


def get_pacific_now():
    tz_pacifc = pytz.timezone("America/Los_Angeles")
    return dates_helper.utc_to_tz_datetime(dates_helper.utc_now(), tz_pacifc)


def get_current_ad_group_id():
    today = get_pacific_now().date()
    return (
        models.AdGroupRotation.objects.filter(ad_group__campaign_id=config.AUTOMATION_CAMPAIGN, start_date__lte=today)
        .latest("start_date")
        .ad_group_id
    )


def get_s3_keys(date=None, s3=None):
    if not s3:
        s3 = boto3.client("s3")

    keys = []
    prefix = "uploads/"
    if date:
        prefix += "{}/{:02d}/{:02d}".format(date.year, date.month, date.day)

    objects = s3.list_objects(Bucket="businesswire-articles", Prefix=prefix)
    while "Contents" in objects and len(objects["Contents"]) > 0:
        keys.extend(k["Key"] for k in objects["Contents"])
        objects = s3.list_objects(Bucket="businesswire-articles", Prefix=prefix, Marker=objects["Contents"][-1]["Key"])

    return keys


def get_s3_keys_for_dates(dates):
    s3 = boto3.client("s3")

    keys = []
    for date in dates:
        keys.extend(get_s3_keys(date=date, s3=s3))
    return keys


def get_s3_key_dt(key):
    parts = _parse_key(key)
    return datetime.datetime(
        int(parts["year"]), int(parts["month"]), int(parts["day"]), int(parts["hour"]), int(parts["minute"])
    )


def get_s3_key_label(key):
    parts = _parse_key(key)
    return parts["news_item_id"]


def _parse_key(key):
    m = REGEX_KEY_PARTS.match(key)
    if not m:
        raise Exception("Couldn't parse key. key={}".format(key))

    return m.groupdict()
