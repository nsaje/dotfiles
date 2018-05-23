import django.db.models

from rest_framework import serializers

import dash.models
from utils import validation_helper


class NotProvided(object):
    def __getitem__(self, key):
        return self

    def __iter__(self):
        # empty iterator pattern: yield keyword turns the function into a generator,
        # a preceding return makes sure the generator is empty
        return
        yield


NOT_PROVIDED = NotProvided()


class BlankToNoneFieldMixin:
    def run_validation(self, value):
        if value == '':
            value = None
        return super().run_validation(value)


class NoneToBlankFieldMixin:
    def run_validation(self, value):
        if value is None:
            value = ''
        return super().run_validation(value)


class NoneToListFieldMixin:
    def run_validation(self, value):
        if value is None:
            value = []
        return super().run_validation(value)


class OutNoneFieldMixin:
    def get_initial(self):
        return super().get_initial() or None


class IdField(serializers.Field):
    def to_representation(self, data):
        if isinstance(data, django.db.models.Model):
            return str(data.id)
        return str(data)

    def to_internal_value(self, data):
        return int(data)


class DashConstantField(serializers.CharField):

    def __init__(self, const_cls, *args, **kwargs):
        self.const_cls = const_cls
        super(DashConstantField, self).__init__(*args, **kwargs)

    def to_internal_value(self, data):
        if data == NOT_PROVIDED:
            return NOT_PROVIDED
        try:
            return getattr(self.const_cls, data)
        except AttributeError:
            valid_choices = self.const_cls.get_all_names()
            raise serializers.ValidationError('Invalid choice %s! Valid choices: %s' % (data, ', '.join(valid_choices)))

    def to_internal_value_many(self, data):
        if data == NOT_PROVIDED:
            return NOT_PROVIDED
        return [self.to_internal_value(x) for x in data]

    def to_representation(self, value):
        if value is None:
            return None
        return self.const_cls.get_name(value)

    def to_representation_many(self, data):
        return [self.to_representation(x) for x in data]


class SourceIdSlugField(serializers.Field):

    def to_internal_value(self, data):
        if isinstance(data, dash.models.Source):
            return data
        try:
            if data.startswith('b1_'):
                data = data[3:]
            source = dash.models.Source.objects.get(bidder_slug=data)
            return source
        except AttributeError:
            self.fail('invalid_choice', data)

    def to_representation(self, source):
        return source.bidder_slug


class PlainCharField(serializers.CharField):
    def to_internal_value(self, data):
        validation_helper.validate_plain_text(data)
        return super(PlainCharField, self).to_internal_value(data)


class BlankIntegerField(BlankToNoneFieldMixin, serializers.IntegerField):
    pass


class BlankDateField(BlankToNoneFieldMixin, serializers.DateField):
    pass


class BlankDecimalField(BlankToNoneFieldMixin, serializers.DecimalField):
    pass


class TwoWayBlankDecimalField(BlankToNoneFieldMixin, serializers.DecimalField):
    def __init__(self, output_precision=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if output_precision is None:
            self.output_precision = self.decimal_places
        else:
            self.output_precision = output_precision

    def to_representation(self, value):
        input_precision = self.decimal_places
        self.decimal_places = self.output_precision
        value = super().to_representation(value)
        self.decimal_places = input_precision
        return value

    def get_initial(self):
        initial = super().get_initial()
        if initial is None:
            return ''
        return initial


class NullPlainCharField(NoneToBlankFieldMixin, PlainCharField):
    pass


class NullListField(NoneToListFieldMixin, serializers.ListField):
    pass


class OutNullDashConstantField(OutNoneFieldMixin, DashConstantField):
    pass


class OutNullURLField(OutNoneFieldMixin, serializers.URLField):
    pass


class OutIntIdField(IdField):
    def to_representation(self, data):
        if isinstance(data, django.db.models.Model):
            return int(data.id)
        return int(data)
