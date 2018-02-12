from django.db.models import Func
from django.core.exceptions import ValidationError


class Round(Func):
    function = 'ROUND'
    template = '%(function)s(%(expressions)s, 0)'


class Coalesce(Func):
    function = 'COALESCE'
    template = '%(function)s(%(expressions)s, 0)'


def validate(*validators):
    errors = {}
    for v in validators:
        try:
            v()
        except ValidationError as e:
            errors[v.__name__.replace('validate_', '')] = e.error_list
    if errors:
        raise ValidationError(errors)
