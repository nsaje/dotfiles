import json

from django import forms
from rest_framework import serializers


class RestFrameworkSerializer(forms.Field):
    def __init__(self, rest_serializer_cls, **kwargs):
        super(RestFrameworkSerializer, self).__init__(**kwargs)
        self.rest_serializer_cls = rest_serializer_cls

    def clean(self, value):
        value = super(RestFrameworkSerializer, self).clean(value)
        serializer = self.rest_serializer_cls(data=value)

        try:
            if not serializer.is_valid():
                if "non_field_errors" in serializer.errors:
                    raise forms.ValidationError(serializer.errors["non_field_errors"])

                raise forms.ValidationError(json.dumps(serializer.errors))
            return serializer.validated_data

        except serializers.ValidationError as e:
            raise forms.ValidationError(e.message)


class RestFrameworkField(forms.Field):
    def __init__(self, rest_field, **kwargs):
        super(RestFrameworkField, self).__init__(**kwargs)
        self.rest_field = rest_field

    def clean(self, value):
        try:
            return self.rest_field.run_validation(value)
        except serializers.ValidationError as e:
            raise forms.ValidationError(e.detail)
