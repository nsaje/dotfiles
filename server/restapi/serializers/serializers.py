import warnings

from rest_framework import serializers
from djangorestframework_camel_case.util import camel_to_underscore
from django.http.request import QueryDict

import utils.list_helper


class QueryParamsExpectations(serializers.Serializer):
    def __init__(self, *args, **kwargs):
        data = kwargs.pop("data")
        assert type(data) == QueryDict, "QueryParamsExpectations should only be used for query parameters validation!"
        kwargs["data"] = QueryDict()
        if data:
            snake_cased_data = QueryDict(mutable=True)
            for key in data:
                snake_cased_key = camel_to_underscore(key)
                value = data.getlist(key)
                if isinstance(self.fields[snake_cased_key], serializers.ListField):
                    value = utils.list_helper.flatten(x.split(",") for x in value)
                snake_cased_data.setlist(snake_cased_key, value)
            kwargs["data"] = snake_cased_data
        super(QueryParamsExpectations, self).__init__(*args, **kwargs)


class PermissionedFieldsMixin(object):
    """
    A serializer mixin that takes a `request` argument and info about permissions on Meta,
    then controls which fields should be displayed.
    """

    @property
    def fields(self):
        fields = super().fields

        if not hasattr(self, "_context"):
            return fields

        if not hasattr(self.Meta, "permissioned_fields"):
            return fields

        try:
            request = self.context["request"]
        except KeyError:
            warnings.warn("Context does not have access to request")
            return fields

        for field, permission in self.Meta.permissioned_fields.items():
            if not request.user.has_perm(permission):
                fields.pop(field, None)

        return fields


class DataNodeSerializerMixin(object):
    @property
    def data(self):
        return {"data": super(DataNodeSerializerMixin, self).data}


class DataNodeListSerializer(DataNodeSerializerMixin, serializers.ListSerializer):
    pass


class NoneToDictSerializerMixin(serializers.Serializer):
    def run_validation(self, data):
        if data is None:
            data = {}
        return super().run_validation(data)
