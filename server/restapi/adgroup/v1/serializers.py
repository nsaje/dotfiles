import decimal

import pytz
import rest_framework.serializers

import core.models.settings
import restapi.serializers.base
import restapi.serializers.fields
import restapi.serializers.serializers
import restapi.serializers.targeting
from dash import constants


class AdGroupGeoSerializer(restapi.serializers.base.RESTAPIBaseSerializer):
    included = restapi.serializers.targeting.TargetRegionsSerializer(
        source="target_regions", allow_null=True, required=False
    )
    excluded = restapi.serializers.targeting.TargetRegionsSerializer(
        source="exclusion_target_regions", allow_null=True, required=False
    )


class AdGroupInterestSerializer(restapi.serializers.base.RESTAPIBaseSerializer):
    included = rest_framework.serializers.ListField(
        child=restapi.serializers.fields.DashConstantField(constants.InterestCategory),
        source="interest_targeting",
        allow_null=True,
        required=False,
    )
    excluded = rest_framework.serializers.ListField(
        child=restapi.serializers.fields.DashConstantField(constants.InterestCategory),
        source="exclusion_interest_targeting",
        allow_null=True,
        required=False,
    )


class AdGroupPublisherGroupsSerializer(restapi.serializers.base.RESTAPIBaseSerializer):
    included = restapi.serializers.fields.NullListField(
        child=rest_framework.serializers.IntegerField(), source="whitelist_publisher_groups", required=False
    )
    excluded = restapi.serializers.fields.NullListField(
        child=rest_framework.serializers.IntegerField(), source="blacklist_publisher_groups", required=False
    )


class AdGroupCustomAudiencesSerializer(restapi.serializers.base.RESTAPIBaseSerializer):
    included = restapi.serializers.fields.NullListField(
        child=rest_framework.serializers.IntegerField(), source="audience_targeting", required=False
    )
    excluded = restapi.serializers.fields.NullListField(
        child=rest_framework.serializers.IntegerField(), source="exclusion_audience_targeting", required=False
    )


class AdGroupRetargetingSerializer(restapi.serializers.base.RESTAPIBaseSerializer):
    included = restapi.serializers.fields.NullListField(
        child=rest_framework.serializers.IntegerField(), source="retargeting_ad_groups", required=False
    )
    excluded = restapi.serializers.fields.NullListField(
        child=rest_framework.serializers.IntegerField(), source="exclusion_retargeting_ad_groups", required=False
    )


class AdGroupLanguageSerializer(restapi.serializers.base.RESTAPIBaseSerializer):
    matching_enabled = rest_framework.serializers.BooleanField(
        source="language_targeting_enabled", default=False, required=False
    )


class AdGroupDaypartingSerializer(
    restapi.serializers.serializers.NoneToDictSerializerMixin, restapi.serializers.base.RESTAPIBaseSerializer
):
    sunday = rest_framework.serializers.ListField(child=rest_framework.serializers.IntegerField(), required=False)
    monday = rest_framework.serializers.ListField(child=rest_framework.serializers.IntegerField(), required=False)
    tuesday = rest_framework.serializers.ListField(child=rest_framework.serializers.IntegerField(), required=False)
    wednesday = rest_framework.serializers.ListField(child=rest_framework.serializers.IntegerField(), required=False)
    thursday = rest_framework.serializers.ListField(child=rest_framework.serializers.IntegerField(), required=False)
    friday = rest_framework.serializers.ListField(child=rest_framework.serializers.IntegerField(), required=False)
    saturday = rest_framework.serializers.ListField(child=rest_framework.serializers.IntegerField(), required=False)
    timezone = restapi.serializers.fields.NullPlainCharField(required=False, allow_blank=True)

    def validate(self, data):
        for key, value in data.items():
            if key == "timezone" and value != "":
                try:
                    pytz.timezone(value)
                except pytz.UnknownTimeZoneError:
                    raise rest_framework.serializers.ValidationError("Invalid timezone: {}".format(value))
            else:
                for hour in value:
                    if hour < 0 or hour > 23:
                        raise rest_framework.serializers.ValidationError("Invalid hour: {}".format(hour))
        return data


class AdGroupTargetingSerializer(
    restapi.serializers.serializers.PermissionedFieldsMixin, restapi.serializers.base.RESTAPIBaseSerializer
):
    class Meta:
        permissioned_fields = {}

    # TODO: PLAC: remove after legacy grace period
    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret["placements"] = ret["environments"]
        return ret

    # TODO: PLAC: remove after legacy grace period
    def to_internal_value(self, data):
        if "environments" not in data and "placements" in data:
            data["environments"] = data["placements"]
        ret = super().to_internal_value(data)
        return ret

    devices = restapi.serializers.targeting.DevicesSerializer(
        source="target_devices",
        allow_empty=False,
        error_messages={"required": "Please select at least one target device."},
    )
    environments = restapi.serializers.targeting.EnvironmentsSerializer(source="target_environments", required=False)
    os = restapi.serializers.targeting.OSsSerializer(source="target_os", required=False)
    browsers = restapi.serializers.targeting.BrowsersSerializer(source="target_browsers", required=False)
    audience = restapi.serializers.targeting.AudienceSerializer(source="bluekai_targeting", required=False)
    geo = AdGroupGeoSerializer(source="*", required=False)
    interest = AdGroupInterestSerializer(source="*", required=False)
    publisher_groups = AdGroupPublisherGroupsSerializer(source="*", required=False)
    custom_audiences = AdGroupCustomAudiencesSerializer(source="*", required=False)
    retargeting_ad_groups = AdGroupRetargetingSerializer(source="*", required=False)
    language = AdGroupLanguageSerializer(source="*", required=False)
    connection_types = restapi.serializers.targeting.ConnectionTypesSerializer(
        source="target_connection_types", required=False
    )


class AdGroupTargetingOenSerializer(AdGroupTargetingSerializer):
    class Meta:
        permissioned_fields = {"browsers_oen": "zemauth.can_use_oen_browser_targeting"}

    browsers_oen = restapi.serializers.targeting.BrowsersSerializer(source="target_browsers", required=False)


class AdGroupAutopilotSerializer(restapi.serializers.base.RESTAPIBaseSerializer):
    state = restapi.serializers.fields.DashConstantField(
        constants.AdGroupSettingsAutopilotState, source="autopilot_state", required=False
    )
    daily_budget = restapi.serializers.fields.TwoWayBlankDecimalField(
        source="local_autopilot_daily_budget",
        max_digits=10,
        decimal_places=4,
        output_precision=2,
        allow_null=True,
        required=False,
        rounding=decimal.ROUND_HALF_DOWN,
    )
    max_bid = restapi.serializers.fields.TwoWayBlankDecimalField(
        source="local_max_autopilot_bid",
        max_digits=10,
        decimal_places=4,
        output_precision=3,
        allow_null=True,
        required=False,
        rounding=decimal.ROUND_HALF_DOWN,
    )


class AdGroupSerializer(
    restapi.serializers.serializers.PermissionedFieldsMixin,
    restapi.serializers.base.RESTAPIBaseSerializer,
    rest_framework.serializers.ModelSerializer,
):
    class Meta:
        model = core.models.settings.AdGroupSettings
        fields = (
            "id",
            "campaign_id",
            "name",
            "bidding_type",
            "bid",
            "state",
            "archived",
            "start_date",
            "end_date",
            "tracking_code",
            "max_cpc",
            "max_cpm",
            "daily_budget",
            "delivery_type",
            "click_capping_daily_ad_group_max_clicks",
            "click_capping_daily_click_budget",
            "dayparting",
            "targeting",
            "autopilot",
            "frequency_capping",
            "additional_data",
        )
        permissioned_fields = {
            "click_capping_daily_click_budget": "zemauth.can_set_click_capping_daily_click_budget",
            "additional_data": "zemauth.can_use_ad_additional_data",
        }

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ad_group = instance.ad_group
        if ad_group and ad_group.bidding_type == constants.BiddingType.CPM:
            ret["max_cpc"] = ""
        elif "max_cpm" in ret:
            ret["max_cpm"] = ""
        return ret

    id = restapi.serializers.fields.IdField(read_only=True, source="ad_group.id")
    campaign_id = restapi.serializers.fields.IdField(source="ad_group.campaign_id")
    name = restapi.serializers.fields.PlainCharField(
        source="ad_group_name", max_length=256, error_messages={"required": "Please specify ad group name."}
    )
    bidding_type = restapi.serializers.fields.DashConstantField(
        constants.BiddingType, source="ad_group.bidding_type", required=False
    )
    state = restapi.serializers.fields.DashConstantField(
        constants.AdGroupSettingsState, default=constants.AdGroupSettingsState.INACTIVE
    )
    archived = rest_framework.serializers.BooleanField(default=False, required=False)
    start_date = rest_framework.serializers.DateField(required=False)
    end_date = restapi.serializers.fields.BlankDateField(required=False, allow_null=True)
    tracking_code = restapi.serializers.fields.NullPlainCharField(required=False, allow_blank=True)
    max_cpc = restapi.serializers.fields.TwoWayBlankDecimalField(
        source="max_cpc_legacy",
        max_digits=10,
        decimal_places=4,
        output_precision=3,
        allow_null=True,
        required=False,
        rounding=decimal.ROUND_HALF_DOWN,
    )
    max_cpm = restapi.serializers.fields.TwoWayBlankDecimalField(
        source="max_cpm_legacy",
        max_digits=10,
        decimal_places=4,
        output_precision=3,
        allow_null=True,
        required=False,
        rounding=decimal.ROUND_HALF_DOWN,
    )
    daily_budget = restapi.serializers.fields.TwoWayBlankDecimalField(
        source="daily_budget_cc",
        max_digits=10,
        decimal_places=4,
        output_precision=2,
        allow_null=True,
        required=False,
        rounding=decimal.ROUND_HALF_DOWN,
    )
    delivery_type = restapi.serializers.fields.DashConstantField(constants.AdGroupDeliveryType, required=False)
    click_capping_daily_ad_group_max_clicks = restapi.serializers.fields.BlankIntegerField(
        allow_null=True, required=False
    )
    click_capping_daily_click_budget = restapi.serializers.fields.BlankDecimalField(
        max_digits=10, decimal_places=4, allow_null=True, required=False, rounding=decimal.ROUND_HALF_DOWN
    )
    dayparting = AdGroupDaypartingSerializer(required=False, allow_null=True)
    targeting = AdGroupTargetingOenSerializer(source="*", required=False)
    autopilot = AdGroupAutopilotSerializer(source="*", required=False)
    frequency_capping = restapi.serializers.fields.BlankIntegerField(allow_null=True, required=False)
    additional_data = rest_framework.fields.JSONField(allow_null=True, required=False)
    bid = restapi.serializers.fields.TwoWayBlankDecimalField(
        source="local_bid",
        max_digits=10,
        decimal_places=4,
        output_precision=3,
        allow_null=False,
        required=False,
        rounding=decimal.ROUND_HALF_DOWN,
    )


class AdGroupQueryParams(
    restapi.serializers.serializers.QueryParamsExpectations, restapi.serializers.serializers.PaginationParametersMixin
):
    campaign_id = restapi.serializers.fields.IdField(required=False)
    account_id = restapi.serializers.fields.IdField(required=False)
    include_archived = rest_framework.serializers.BooleanField(default=False, required=False)
