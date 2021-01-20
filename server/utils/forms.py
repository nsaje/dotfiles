from django import forms
from django.core.exceptions import ValidationError


class EmptyChoiceField(forms.ChoiceField):
    def __init__(self, *, choices=(), empty_label=None, **kwargs):
        if empty_label is not None:
            choices = tuple([(u"", empty_label)] + list(choices))
        super().__init__(choices=choices, **kwargs)


class IntegerChoiceField(forms.ChoiceField):
    def to_python(self, value):
        if value is None:
            return None
        return int(value)


class IntegerEmptyChoiceField(EmptyChoiceField):
    def to_python(self, value):
        if value is None or value in self.empty_values:
            return None
        return int(value)


class IntegerMultipleChoiceField(forms.MultipleChoiceField):
    def to_python(self, value):
        if not value:
            return []
        elif not isinstance(value, (list, tuple)):
            raise ValidationError(self.error_messages["invalid_list"], code="invalid_list")
        return sorted([int(v) for v in value])
