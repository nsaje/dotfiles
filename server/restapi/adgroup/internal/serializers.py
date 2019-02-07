import rest_framework.serializers

import restapi.serializers.base
import restapi.serializers.hack
import restapi.serializers.targeting


class ExtraDataDefaultSettingsSerializer(restapi.serializers.base.RESTAPIBaseSerializer):
    target_regions = restapi.serializers.targeting.TargetRegionsSerializer(required=False, allow_null=True)
    exclusion_target_regions = restapi.serializers.targeting.TargetRegionsSerializer(required=False, allow_null=True)
    target_devices = restapi.serializers.targeting.DevicesSerializer(required=False, allow_null=True)
    target_os = restapi.serializers.targeting.OSsSerializer(required=False, allow_null=True)
    target_placements = restapi.serializers.targeting.PlacementsSerializer(required=False, allow_null=True)


class ExtraDataRetargetableAdGroupSerializer(restapi.serializers.base.RESTAPIBaseSerializer):
    id = rest_framework.serializers.IntegerField(required=False)
    archived = rest_framework.serializers.BooleanField(default=False, required=False)
    campaign_name = rest_framework.serializers.CharField(required=False)
    name = rest_framework.serializers.CharField(required=False)


class ExtraDataAudiencesSerializer(restapi.serializers.base.RESTAPIBaseSerializer):
    id = rest_framework.serializers.IntegerField(required=False)
    archived = rest_framework.serializers.BooleanField(default=False, required=False)
    name = rest_framework.serializers.CharField(required=False)


class ExtraDataRetargetingSerializer(restapi.serializers.base.RESTAPIBaseSerializer):
    sources = rest_framework.serializers.ListField(child=restapi.serializers.fields.PlainCharField(), allow_empty=True)


class ExtraDataWarningSerializer(restapi.serializers.base.RESTAPIBaseSerializer):
    retargeting = ExtraDataRetargetingSerializer(required=False, allow_null=True)


class ExtraDataSerializer(restapi.serializers.base.RESTAPIBaseSerializer):
    action_is_waiting = rest_framework.serializers.BooleanField(default=False, required=False)
    can_archive = rest_framework.serializers.BooleanField(default=False, required=False)
    can_restore = rest_framework.serializers.BooleanField(default=False, required=False)
    default_settings = ExtraDataDefaultSettingsSerializer(default=False, required=False)
    retargetable_adgroups = rest_framework.serializers.ListField(
        child=ExtraDataRetargetableAdGroupSerializer(), allow_empty=True
    )
    audiences = rest_framework.serializers.ListField(child=ExtraDataAudiencesSerializer(), allow_empty=True)
    warnings = ExtraDataWarningSerializer(required=False, allow_null=True)
    hacks = rest_framework.serializers.ListField(child=restapi.serializers.hack.HackSerializer(), allow_empty=True)
