import django.db.models

from rest_framework import serializers
from rest_framework import fields

import utils.list_helper


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
        return map(lambda x: self.to_internal_value(x), data)

    def to_representation(self, value):
        if value is None:
            return None
        return self.const_cls.get_name(value)

    def to_representation_many(self, data):
        return map(lambda x: self.to_representation(x), data)


class CommaListField(fields.ListField):
    """ Allows list query parameters in the form of both
        ?param=1,2,3 and ?param=1&param=2&param=3
    """

    def __init__(self, *args, **kwargs):
        self.child = kwargs.pop('child')
        return super(CommaListField, self).__init__(*args, **kwargs)

    def get_value(self, dictionary):
        """Split by commas"""
        unsplit_data = super(CommaListField, self).get_value(dictionary)
        data = utils.list_helper.flatten(x.split(',') for x in unsplit_data)
        return data
