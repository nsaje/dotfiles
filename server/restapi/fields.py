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
