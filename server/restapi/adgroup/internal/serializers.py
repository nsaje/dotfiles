import decimal

import rest_framework.serializers

import dash.constants
import restapi.adgroup.v1.serializers
import restapi.directdeal.internal.serializers
import restapi.serializers.base
import restapi.serializers.deals
import restapi.serializers.fields
import restapi.serializers.hack
import restapi.serializers.targeting


class ExtraDataDefaultSettingsSerializer(restapi.serializers.base.RESTAPIBaseSerializer):
    target_regions = restapi.serializers.targeting.TargetRegionsSerializer(required=False, allow_null=True)
    exclusion_target_regions = restapi.serializers.targeting.TargetRegionsSerializer(required=False, allow_null=True)
    target_devices = restapi.serializers.targeting.DevicesSerializer(required=False, allow_null=True)
    target_os = restapi.serializers.targeting.OSsSerializer(required=False, allow_null=True)
    target_placements = restapi.serializers.targeting.PlacementsSerializer(required=False, allow_null=True)


class ExtraDataRetargetableAdGroupSerializer(restapi.serializers.base.RESTAPIBaseSerializer):
    id = restapi.serializers.fields.IdField(required=False)
    archived = rest_framework.serializers.BooleanField(default=False, required=False)
    campaign_name = rest_framework.serializers.CharField(required=False)
    name = rest_framework.serializers.CharField(required=False)


class ExtraDataAudiencesSerializer(restapi.serializers.base.RESTAPIBaseSerializer):
    id = restapi.serializers.fields.IdField(required=False)
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
    is_campaign_autopilot_enabled = rest_framework.serializers.BooleanField(default=False, required=False)
    account_id = restapi.serializers.fields.IdField(required=False)
    currency = restapi.serializers.fields.DashConstantField(
        dash.constants.Currency, default=dash.constants.Currency.USD, required=False
    )
    optimization_objective = restapi.serializers.fields.DashConstantField(
        dash.constants.CampaignGoalKPI, required=False
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
    deals = rest_framework.serializers.ListField(
        child=restapi.serializers.deals.DealSerializer(), default=[], allow_empty=True
    )


class AdGroupAutopilotSerializer(restapi.adgroup.v1.serializers.AdGroupAutopilotSerializer):
    # NOTE: extend daily_budget v1 field serializer to reject
    # None or empty values and values lower than zero.
    daily_budget = restapi.serializers.fields.TwoWayBlankDecimalField(
        source="local_autopilot_daily_budget",
        max_digits=10,
        decimal_places=4,
        output_precision=2,
        rounding=decimal.ROUND_HALF_DOWN,
        required=False,
        min_value=0,
    )


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
            "redirect_pixel_urls",
            "redirect_javascript",
            "tracking_code",
            "max_cpc",
            "max_cpm",
            "delivery_type",
            "click_capping_daily_ad_group_max_clicks",
            "dayparting",
            "targeting",
            "autopilot",
            "manage_rtb_sources_as_one",
            "frequency_capping",
            "notes",
            "deals",
        )
        permissioned_fields = {
            "click_capping_daily_ad_group_max_clicks": "zemauth.can_set_click_capping",
            "click_capping_daily_click_budget": "zemauth.can_set_click_capping_daily_click_budget",
            "frequency_capping": "zemauth.can_set_frequency_capping",
            "additional_data": "zemauth.can_use_ad_additional_data",
            "deals": "zemauth.can_see_deals_in_ui",
        }

    redirect_pixel_urls = restapi.serializers.fields.NullListField(
        child=rest_framework.serializers.CharField(), required=False
    )
    redirect_javascript = rest_framework.serializers.CharField(required=False, allow_blank=True)
    manage_rtb_sources_as_one = rest_framework.serializers.BooleanField(source="b1_sources_group_enabled")
    notes = rest_framework.serializers.CharField(read_only=True)
    autopilot = AdGroupAutopilotSerializer(source="*", required=False)
    deals = rest_framework.serializers.ListSerializer(
        child=restapi.directdeal.internal.serializers.DirectDealSerializer(), default=[], allow_empty=True
    )
