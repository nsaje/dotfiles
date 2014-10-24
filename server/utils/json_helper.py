# -*- coding: utf-8 -*-
import datetime
import decimal
import json
import pytz

from django.conf import settings


class JSONEncoder(json.JSONEncoder):
    def __init__(self, convert_datetimes=True, **kwargs):
        self.convert_datetimes = convert_datetimes
        super(JSONEncoder, self).__init__(**kwargs)

    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            if not self.convert_datetimes:
                return obj.isoformat()

            if obj.tzinfo is None:
                # naive datetimes are treated as UTC
                obj = pytz.utc.localize(obj)

            return obj.astimezone(pytz.timezone(settings.TIMEZONE)).\
                replace(tzinfo=None).isoformat()

        elif isinstance(obj, (datetime.date, datetime.time)):
            return obj.isoformat()
        elif isinstance(obj, decimal.Decimal):
            return str(obj)
        else:
            return json.JSONEncoder.default(self, obj)
