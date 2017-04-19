import sys
import rest_framework.serializers
import restapi.fields
import dash.constants


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
