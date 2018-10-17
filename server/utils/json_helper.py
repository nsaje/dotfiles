# -*- coding: utf-8 -*-
import datetime
import decimal
import json
import pytz
import uuid


class JSONEncoder(json.JSONEncoder):
    def __init__(self, convert_datetimes_tz=None, **kwargs):
        self.convert_datetimes_tz = convert_datetimes_tz
        super(JSONEncoder, self).__init__(**kwargs)

    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            if self.convert_datetimes_tz is None:
                return obj.isoformat()

            if obj.tzinfo is None:
                # naive datetimes are treated as UTC
                obj = pytz.utc.localize(obj)

            return obj.astimezone(pytz.timezone(self.convert_datetimes_tz)).replace(tzinfo=None).isoformat()

        elif isinstance(obj, (datetime.date, datetime.time)):
            return obj.isoformat()
        elif isinstance(obj, decimal.Decimal):
            return str(obj)
        elif isinstance(obj, uuid.UUID):
            return str(obj)
        else:
            return json.JSONEncoder.default(self, obj)


def json_serializable_changes(changes):
    if not changes:
        return
    ret = {}
    for key, value in changes.items():
        if hasattr(value, "id"):
            ret[key] = value.id
        else:
            ret[key] = value
    return ret
