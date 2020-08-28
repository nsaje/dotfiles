import warnings
from collections import OrderedDict

from django.http.request import QueryDict
from djangorestframework_camel_case.util import camel_to_underscore
from rest_framework import serializers

import restapi.serializers.fields
import utils.exc
import utils.list_helper
import zemauth.models


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
                if isinstance(self.fields.get(snake_cased_key), serializers.ListField):
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


class EntityPermissionedFieldsMixin(object):
    """
    A serializer mixin that takes a `request` argument and info about entity permissions on Meta,
    then controls which fields should be displayed.
    """

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if not hasattr(self.Meta, "entity_permissioned_fields"):
            return data

        ret = OrderedDict()
        for field in data.keys():
            if self.has_entity_permission_on_field(field, data):
                ret[field] = data[field]
        return ret

    def to_internal_value(self, data):
        if not hasattr(self.Meta, "entity_permissioned_fields"):
            return super().to_internal_value(data)

        ret = OrderedDict()
        for field in data.keys():
            if self.has_entity_permission_on_field(field, data):
                ret[field] = data[field]
            elif self.fields.get(field) is not None:
                self.fields.pop(field)
        return super().to_internal_value(ret)

    def has_entity_permission_on_field(self, field: str, data: OrderedDict) -> bool:
        try:
            request = self.context["request"]
        except KeyError:
            warnings.warn("Context does not have access to request")
            return True

        config = self.Meta.entity_permissioned_fields.get("config")
        if config is None:
            return True

        fields = self.Meta.entity_permissioned_fields.get("fields")
        if fields is None:
            return True

        permission = fields.get(field)
        if permission is None:
            return True

        return self.has_entity_permission(request.user, permission, config, data)

    def has_entity_permission(
        self, user: zemauth.models.User, permission: OrderedDict, config: OrderedDict, data: OrderedDict
    ) -> bool:
        entity_id_getter_fn = config.get("entity_id_getter_fn")
        if entity_id_getter_fn is None:
            return True

        entity_access_fn = config.get("entity_access_fn")
        if entity_access_fn is None:
            return True

        if user.has_perm("zemauth.fea_use_entity_permission"):
            try:
                entity_id = entity_id_getter_fn(data)
                entity_access_fn(user, permission["permission"], entity_id)
                return True
            except utils.exc.MissingDataError:
                return False
        return user.has_perm(permission["fallback_permission"])


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


class PaginationParametersMixin(serializers.Serializer):
    limit = restapi.serializers.fields.IntegerField(required=False)
    offset = restapi.serializers.fields.IntegerField(required=False)
    marker = restapi.serializers.fields.IntegerField(required=False)
