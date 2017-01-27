import pytz
from django import forms
from django.contrib.postgres import forms as postgres_forms


class DayField(forms.Field):

    def clean(self, value):
        super(DayField, self).clean(value)

        if not value:
            return

        if not isinstance(value, list):
            raise forms.ValidationError('Value must be an instance of list')

        for hour in value:
            if hour < 0 or hour > 23:
                raise forms.ValidationError('Invalid hour {}'.format(hour))


class TimeZoneField(forms.Field):

    def clean(self, value):
        super(TimeZoneField, self).clean(value)

        if not value:
            return

        try:
            pytz.timezone(value)
        except pytz.UnknownTimeZoneError:
            raise forms.ValidationError('Invalid timezone: ', value)


class DaypartingField(forms.Field):
    sunday = DayField(required=False)
    monday = DayField(required=False)
    tuesday = DayField(required=False)
    wednesday = DayField(required=False)
    thursday = DayField(required=False)
    friday = DayField(required=False)
    saturday = DayField(required=False)

    timezone = TimeZoneField(required=False)


class TargetingExpressionField(forms.Field):

    def validate(self, value):
        super(TargetingExpressionField, self).validate(value)
        self._clean_targeting_expression(value)

    @classmethod
    def _clean_targeting_expression(cls, exp):
        if not exp:
            return
        if isinstance(exp, list):  # ['and', 'bluekai:123', ['not', 'bluekai:321']]
            if exp[0] not in ['and', 'or', 'not']:
                raise forms.ValidationError(message='Targeting expression operator %s not valid' % exp[0])
            for subexp in exp[1:]:
                cls._clean_targeting_expression(subexp)
        elif isinstance(exp, basestring):  # 'bluekai:123'
            try:
                tokens = exp.split(':', 1)
                assert len(tokens) == 2
                # lr example: lr-IntuitTurbo:45936607
                assert 'lr-' == exp[:3] or tokens[0] in ['bluekai', 'liveramp', 'outbrain']
            except:
                raise forms.ValidationError('Invalid category format: "%s"' % exp)
        else:
            raise forms.ValidationError(message='Invalid item "%s" in the targeting expression.' % exp)
