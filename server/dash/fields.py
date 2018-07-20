import pytz
from django import forms


class DayField(forms.Field):
    def clean(self, value):
        super(DayField, self).clean(value)

        if not value:
            return

        if not isinstance(value, list):
            raise forms.ValidationError("Value must be an instance of list")

        for hour in value:
            if hour < 0 or hour > 23:
                raise forms.ValidationError("Invalid hour {}".format(hour))


class TimeZoneField(forms.Field):
    def clean(self, value):
        super(TimeZoneField, self).clean(value)

        if not value:
            return

        try:
            pytz.timezone(value)
        except pytz.UnknownTimeZoneError:
            raise forms.ValidationError("Invalid timezone: ", value)


class DaypartingField(forms.Field):
    sunday = DayField(required=False)
    monday = DayField(required=False)
    tuesday = DayField(required=False)
    wednesday = DayField(required=False)
    thursday = DayField(required=False)
    friday = DayField(required=False)
    saturday = DayField(required=False)

    timezone = TimeZoneField(required=False)
