import sys

import rest_framework.serializers
from django.utils import six

import dash.constants
import dash.models
import dash.regions
import restapi.serializers.fields


class VersionSerializer(rest_framework.serializers.Serializer):
    min = restapi.serializers.fields.DashConstantField(dash.constants.OperatingSystemVersion, required=False)
    max = restapi.serializers.fields.DashConstantField(dash.constants.OperatingSystemVersion, required=False)

    def validate(self, data):
        # Validation done in OSSerializer
        return data


class OSSerializer(rest_framework.serializers.Serializer):
    name = restapi.serializers.fields.DashConstantField(dash.constants.OperatingSystem)
    version = VersionSerializer(required=False)

    def validate(self, data):
        versions = dash.constants.OSV_MAPPING.get(data["name"], [])
        version = data["version"] if "version" in data else {}
        try:
            min_idx = versions.index(version["min"]) if "min" in version else 0
            max_idx = versions.index(version["max"]) if "max" in version else sys.maxsize

            if min_idx > max_idx:
                raise rest_framework.serializers.ValidationError("Max version must be greater or equal to min version.")
        except ValueError:
            raise rest_framework.serializers.ValidationError("Unknown OS version")

        return data


class OSsSerializer(rest_framework.serializers.ListSerializer):
    def __init__(self, *args, **kwargs):
        self.child = OSSerializer()
        kwargs["allow_null"] = True
        super(OSsSerializer, self).__init__(*args, **kwargs)


class BrowserSerializer(rest_framework.serializers.Serializer):
    family = restapi.serializers.fields.DashConstantField(dash.constants.BrowserFamily)


class BrowsersSerializer(rest_framework.serializers.ListSerializer):
    def __init__(self, *args, **kwargs):
        self.child = BrowserSerializer()
        kwargs["allow_null"] = True
        super().__init__(*args, **kwargs)


class EnvironmentsSerializer(rest_framework.serializers.ListSerializer):
    def __init__(self, *args, **kwargs):
        self.child = restapi.serializers.fields.DashConstantField(dash.constants.AdTargetEnvironment)
        kwargs["allow_null"] = True
        super(EnvironmentsSerializer, self).__init__(*args, **kwargs)


class DevicesSerializer(rest_framework.serializers.ListSerializer):
    def __init__(self, *args, **kwargs):
        kwargs["allow_null"] = True
        self.child = restapi.serializers.fields.DashConstantField(dash.constants.AdTargetDevice)
        super(DevicesSerializer, self).__init__(*args, **kwargs)


class AudienceSerializer(rest_framework.serializers.BaseSerializer):
    operators = ("and", "not", "or")
    types = (
        "bluekai",
        "outbrain",
        "lotame",
        "obs",
        "obi",
        "obl",
        "videocdn",
        "weborama",
        "ob-eyeota",
        "ob-nielsen",
        "neodata",
    )

    def __init__(self, *args, **kwargs):
        self.use_list_repr = kwargs.pop("use_list_repr", False)
        super(AudienceSerializer, self).__init__(*args, **kwargs)

    def _to_representation_recur(self, obj):
        if isinstance(obj, six.string_types):
            return {"category": obj}
        if not obj:
            return {}
        op, exp = obj[0], obj[1:]
        return {op.upper(): [self._to_representation_recur(subexp) for subexp in exp]}

    def to_representation(self, obj):
        if self.use_list_repr:
            return obj

        return self._to_representation_recur(obj)

    def _is_leaf_node(self, data):
        if not isinstance(data, dict):
            return False
        return "category" in data

    def _handle_leaf_node(self, data):
        exp = data["category"]
        tokens = exp.split(":", 1)
        if len(tokens) != 2 or (tokens[0][:3] != "lr-" and tokens[0] not in self.types):
            raise rest_framework.serializers.ValidationError('Invalid category format: "{}"'.format(exp))
        return exp

    def _handle_expression(self, data):
        if len(data) != 1:
            raise rest_framework.serializers.ValidationError(
                "Invalid expression - expected one operator, "
                "got [{}]".format(", ".join(str(k) for k in list(data.keys())))
            )

        op, exp = list(data.items())[0]
        if op.lower() not in self.operators:
            raise rest_framework.serializers.ValidationError('Invalid expression - unknown operator "{}"'.format(op))

        if not exp:
            raise rest_framework.serializers.ValidationError(
                "Invalid expression - empty subexpression " 'for operator "{}"'.format(op)
            )

        if op.lower() == "not" and len(exp) != 1:
            raise rest_framework.serializers.ValidationError(
                "Invalid expression - NOT has to have exactly one child node"
            )

        return [op.lower()] + [self._to_internal_recur(subexp) for subexp in exp]

    def _to_internal_recur(self, data):
        if not isinstance(data, dict):
            raise rest_framework.serializers.ValidationError("Invalid expression - elements of lists should be objects")

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


_geo_type_cache = {}


class TargetRegionsSerializer(rest_framework.serializers.Serializer):
    countries = rest_framework.serializers.ListField(child=restapi.serializers.fields.PlainCharField(), required=False)
    regions = rest_framework.serializers.ListField(child=restapi.serializers.fields.PlainCharField(), required=False)
    dma = rest_framework.serializers.ListField(child=restapi.serializers.fields.PlainCharField(), required=False)
    cities = rest_framework.serializers.ListField(child=restapi.serializers.fields.PlainCharField(), required=False)
    postal_codes = rest_framework.serializers.ListField(
        child=restapi.serializers.fields.PlainCharField(), required=False
    )

    default_error_messages = {"invalid_choice": '"{input}" is not a valid location.'}

    def validate_countries(self, values):
        return self._validate_geolocations(dash.constants.LocationType.COUNTRY, values)

    def validate_regions(self, values):
        regions = []
        countries = []
        for location in values:
            if (
                location in dash.regions.SUBDIVISION_TO_COUNTRY
            ):  # we used to treat Puerto Rico, Guam etc. as subdivisions
                countries.append(dash.regions.SUBDIVISION_TO_COUNTRY[location])
            else:
                regions.append(location)
        self._validate_geolocations(dash.constants.LocationType.REGION, regions)
        self._validate_geolocations(dash.constants.LocationType.COUNTRY, countries)
        return regions + countries

    def validate_dma(self, values):
        return self._validate_geolocations(dash.constants.LocationType.DMA, values)

    def validate_cities(self, values):
        return self._validate_geolocations(dash.constants.LocationType.CITY, values)

    def validate_postal_codes(self, values):
        zip_countries = []
        for location in values:
            zip_tokenized = location.rsplit(":", 1)
            if len(zip_tokenized) > 1:  # a ZIP code, need to check country
                zip_countries.append(zip_tokenized[0])
            else:
                self.fail("invalid_choice", input=location)
        self._validate_geolocations(dash.constants.LocationType.COUNTRY, zip_countries)
        return values

    def _validate_geolocations(self, geo_type, values):
        qs = dash.models.Geolocation.objects.filter(type=geo_type, pk__in=values)
        valid_keys = set(location.key for location in qs)
        for key in values:
            if key not in valid_keys:
                self.fail("invalid_choice", input=key)
        return values

    def validate(self, attrs):
        data = super(TargetRegionsSerializer, self).validate(attrs)
        return [location for location_list in list(data.values()) for location in location_list if location_list]

    def _get_geo_types(self, target_regions):
        locations_to_fetch = [loc for loc in target_regions if loc not in _geo_type_cache]

        if locations_to_fetch:
            non_zips = {
                loc.key: loc for loc in dash.features.geolocation.Geolocation.objects.filter(key__in=locations_to_fetch)
            }
            zips = set(target_regions) - set(non_zips.keys())
            for loc in locations_to_fetch:
                geo_type = None
                if loc in non_zips:
                    geo_type = non_zips[loc].type
                if loc in zips:
                    geo_type = dash.constants.LocationType.ZIP

                _geo_type_cache[loc] = geo_type

        results = []
        for loc in target_regions:
            geo_type = _geo_type_cache[loc]
            results.append((loc, geo_type))
        return results

    def to_representation(self, target_regions):
        geo = {"countries": [], "regions": [], "dma": [], "cities": [], "postal_codes": []}

        for location, geo_type in self._get_geo_types(target_regions):
            if geo_type == dash.constants.LocationType.COUNTRY:
                geo["countries"].append(location)
            elif geo_type == dash.constants.LocationType.REGION:
                geo["regions"].append(location)
            elif geo_type == dash.constants.LocationType.DMA:
                geo["dma"].append(location)
            elif geo_type == dash.constants.LocationType.CITY:
                geo["cities"].append(location)
            elif geo_type == dash.constants.LocationType.ZIP:
                geo["postal_codes"].append(location)
            else:
                raise AttributeError("Invalid geo type: {}".format(geo_type))

        # TODO hamax: field serializer is extremely slow when Serializer objects is initialized for each instance separately.
        # For now we'll trust this function to return correct data.
        # return super(TargetRegionsSerializer, self).to_representation(geo)
        return geo
