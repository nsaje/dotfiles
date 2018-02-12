from django.contrib.postgres.forms import JSONField
from django.core.exceptions import ValidationError

from . import model


class CustomFlagsField(JSONField):

    def to_python(self, value):
        return dict((el, True) for el in value)

    def prepare_value(self, value):
        if not value:
            return []
        return list(value.keys())

    def validate(self, value):
        all_flags = set(model.CustomFlag.objects.all().values_list('id', flat=True))

        errors = []
        for i, el in enumerate(value):
            if el not in all_flags:
                errors.append(ValidationError(
                    'Invalid custom flag',
                    code='item_invalid',
                    params={'nth': i},
                ))

        if errors:
            raise ValidationError(errors)
