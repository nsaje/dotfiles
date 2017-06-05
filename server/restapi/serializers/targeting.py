import sys

from django.utils import six
import rest_framework.serializers

import dash.constants
import restapi.fields


class VersionSerializer(rest_framework.serializers.Serializer):
    min = restapi.fields.DashConstantField(dash.constants.OperatingSystemVersion, required=False)
    max = restapi.fields.DashConstantField(dash.constants.OperatingSystemVersion, required=False)

    def validate(self, data):
        # Validation done in OSSerializer
        return data


class OSSerializer(rest_framework.serializers.Serializer):
    name = restapi.fields.DashConstantField(dash.constants.OperatingSystem)
    version = VersionSerializer(required=False)

    def validate(self, data):
        versions = dash.constants.OSV_MAPPING[data['name']]
        version = data['version'] if 'version' in data else {}
        try:
            min_idx = versions.index(version['min']) if 'min' in version else 0
            max_idx = versions.index(version['max']) if 'max' in version else sys.maxint

            if min_idx > max_idx:
                raise rest_framework.serializers.ValidationError('Max version must be greater or equal to min version.')
        except ValueError:
            raise rest_framework.serializers.ValidationError('Unknown OS version')

        return data


class OSsSerializer(rest_framework.serializers.ListSerializer):
    def __init__(self, *args, **kwargs):
        self.child = OSSerializer()
        kwargs['allow_null'] = True
        super(OSsSerializer, self).__init__(*args, **kwargs)


class PlacementsSerializer(rest_framework.serializers.ListSerializer):
    def __init__(self, *args, **kwargs):
        self.child = restapi.fields.DashConstantField(dash.constants.Placement)
        kwargs['allow_null'] = True
        super(PlacementsSerializer, self).__init__(*args, **kwargs)


class DevicesSerializer(rest_framework.serializers.ListSerializer):
    def __init__(self, *args, **kwargs):
        kwargs['allow_null'] = True
        self.child = restapi.fields.DashConstantField(dash.constants.AdTargetDevice)
        super(DevicesSerializer, self).__init__(*args, **kwargs)


class DemographicSerializer(rest_framework.serializers.BaseSerializer):

    operators = ('and', 'not', 'or')
    types = ('bluekai', 'outbrain', 'lotame')

    def _should_use_list_representation(self):
        if 'request' not in self.context:
            return True
        return not self.context['request'].user.has_perm(
            'zemauth.can_use_bluekai_targeting')

    def _to_representation_recur(self, obj):
        if isinstance(obj, six.string_types):
            return {'category': obj}
        if not obj:
            return {}
        op, exp = obj[0], obj[1:]
        return {
            op.upper(): [self._to_representation_recur(subexp) for subexp in exp]
        }

    def to_representation(self, obj):
        if self._should_use_list_representation():
            return obj

        return self._to_representation_recur(obj)

    def _is_leaf_node(self, data):
        if not isinstance(data, dict):
            return False
        return 'category' in data

    def _handle_leaf_node(self, data):
        exp = data['category']
        tokens = exp.split(':', 1)
        if len(tokens) != 2 or\
           (tokens[0][:3] != 'lr-' and tokens[0] not in self.types):
                raise rest_framework.serializers.ValidationError(
                    'Invalid category format: "{}"'.format(exp)
                )
        return exp

    def _handle_expression(self, data):
        if len(data) != 1:
            raise rest_framework.serializers.ValidationError(
                'Invalid expression - expected exactly '
                'one operator, got {}'.format(len(data))
            )

        op, exp = list(data.items())[0]
        if op.lower() not in self.operators:
            raise rest_framework.serializers.ValidationError(
                'Invalid expression - unknown operator "{}"'.format(op)
            )

        return [op.lower()] +\
            [self._to_internal_recur(subexp) for subexp in exp]

    def _to_internal_recur(self, data):
        if not isinstance(data, dict):
            raise rest_framework.serializers.ValidationError(
                'Invalid expression - elements of lists should be objects'
            )

        if self._is_leaf_node(data):
            ret = self._handle_leaf_node(data)
            return ret
        else:
            return self._handle_expression(data)

    def to_internal_value(self, data):
        if isinstance(data, list):
            # NOTE: a workaround for old restapi uses
            data = self._to_representation_recur(data)

        if not data:
            # NOTE: only accept empty dict on top level
            return []

        return self._to_internal_recur(data)
