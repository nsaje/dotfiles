import rest_framework.serializers
from rest_framework.fields import SkipField
from rest_framework.relations import PKOnlyObject

from collections import OrderedDict


class RESTAPIBaseSerializer(rest_framework.serializers.Serializer):

    def to_representation(self, instance):
        """
        Object instance -> Dict of primitive datatypes.
        Copied from base django rest framework implementation.
        When a field is None, 'get_initial()' was called only when serializer
        was called directly. Now it does the same for nested serializers.
        """
        ret = OrderedDict()
        fields = self._readable_fields

        for field in fields:
            try:
                attribute = field.get_attribute(instance)
            except SkipField:
                continue

            check_for_none = attribute.pk if isinstance(attribute, PKOnlyObject) else attribute
            if check_for_none is None:
                ret[field.field_name] = field.get_initial()
            else:
                ret[field.field_name] = field.to_representation(attribute)

        return ret


class NoneToDictSerializerMixin(rest_framework.serializers.Serializer):

    def run_validation(self, data):
        if data is None:
            data = {}
        return super().run_validation(data)
