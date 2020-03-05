from django.db.models import DateField
from django.db.models.functions import Cast
from django.db.models.functions import ExtractDay
from django.db.models.functions import Now

from ... import constants


def get_days_since_created_field(field):
    return ExtractDay(Cast(Now(), DateField()) - cast_datetime_field_to_date(field))


def cast_datetime_field_to_date(field):
    return Cast(field, DateField())


def map_keys_from_constant_to_qs_string_representation(fields):
    # NOTE: django expects strings as keys in annotations.
    # They are mapped to descriptive names for clarity.
    return {constants.METRIC_SETTINGS_MAPPING[metric]: field for metric, field in fields.items()}
