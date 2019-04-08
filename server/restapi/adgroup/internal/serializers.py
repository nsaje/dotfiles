import rest_framework.serializers

import dash.constants
import restapi.adgroup.v1.serializers
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


class ExtraDataDealSerializer(restapi.serializers.base.RESTAPIBaseSerializer):
    level = rest_framework.serializers.CharField(required=False)
    direct_deal_connection_id = rest_framework.serializers.IntegerField(required=False)
    deal_id = rest_framework.serializers.CharField(required=False)
    source = rest_framework.serializers.CharField(required=False)
    exclusive = rest_framework.serializers.BooleanField(default=False, required=False)
    description = rest_framework.serializers.CharField(required=False)
    is_applied = rest_framework.serializers.BooleanField(default=False, required=False)


class ExtraDataSerializer(restapi.serializers.base.RESTAPIBaseSerializer):
    action_is_waiting = rest_framework.serializers.BooleanField(default=False, required=False)
    can_archive = rest_framework.serializers.BooleanField(default=False, required=False)
    can_restore = rest_framework.serializers.BooleanField(default=False, required=False)
    is_campaign_autopilot_enabled = rest_framework.serializers.BooleanField(default=False, required=False)
    account_id = rest_framework.serializers.IntegerField(required=False)
    currency = restapi.serializers.fields.DashConstantField(
        dash.constants.Currency, default=dash.constants.Currency.USD, required=False
    )
    default_settings = ExtraDataDefaultSettingsSerializer(default=False, required=False)
    retargetable_ad_groups = rest_framework.serializers.ListField(
        child=ExtraDataRetargetableAdGroupSerializer(), allow_empty=True
    )
    audiences = rest_framework.serializers.ListField(child=ExtraDataAudiencesSerializer(), allow_empty=True)
    warnings = ExtraDataWarningSerializer(required=False, allow_null=True)
    hacks = rest_framework.serializers.ListField(
        child=restapi.serializers.hack.HackSerializer(), default=[], allow_empty=True
    )
    deals = rest_framework.serializers.ListField(child=ExtraDataDealSerializer(), default=[], allow_empty=True)


class AdGroupSerializer(restapi.adgroup.v1.serializers.AdGroupSerializer):
    class Meta(restapi.adgroup.v1.serializers.AdGroupSerializer.Meta):
        fields = (
            "id",
            "campaign_id",
            "name",
            "bidding_type",
            "state",
            "archived",
            "start_date",
            "end_date",
            "tracking_code",
            "max_cpc",
            "max_cpm",
            "delivery_type",
            "click_capping_daily_ad_group_max_clicks",
            "dayparting",
            "targeting",
            "autopilot",
            "frequency_capping",
            "notes",
        )

    notes = rest_framework.serializers.CharField(required=False)
