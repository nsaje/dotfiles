import rest_framework.serializers

import restapi.serializers.base
import restapi.serializers.fields
import restapi.serializers.serializers
from dash import constants


class GATrackingSerializer(rest_framework.serializers.Serializer):
    enabled = rest_framework.serializers.NullBooleanField(source="enable_ga_tracking", required=False)
    type = restapi.serializers.fields.DashConstantField(
        constants.GATrackingType, source="ga_tracking_type", required=False
    )
    web_property_id = rest_framework.serializers.RegexField(
        constants.GA_PROPERTY_ID_REGEX,
        source="ga_property_id",
        required=False,
        max_length=25,
        allow_blank=True,
        error_messages={"web_property_id": "Web property ID is not valid."},
    )

    def validate(self, data):
        if (
            data.get("enable_ga_tracking")
            and data.get("ga_tracking_type") == constants.GATrackingType.API
            and not data.get("ga_property_id")
        ):
            raise rest_framework.serializers.ValidationError(
                {"web_property_id": "Web property ID should not be empty."}
            )
        return data


class AdobeTrackingSerializer(rest_framework.serializers.Serializer):
    enabled = rest_framework.serializers.NullBooleanField(source="enable_adobe_tracking", required=False)
    tracking_parameter = restapi.serializers.fields.PlainCharField(
        source="adobe_tracking_param", required=False, max_length=10, allow_blank=True
    )


class CampaignTrackingSerializer(rest_framework.serializers.Serializer):
    ga = GATrackingSerializer(source="*", required=False)
    adobe = AdobeTrackingSerializer(source="*", required=False)


class PublisherGroupsSerializer(rest_framework.serializers.Serializer):
    included = rest_framework.serializers.ListField(
        child=rest_framework.serializers.IntegerField(), source="whitelist_publisher_groups", required=False
    )
    excluded = rest_framework.serializers.ListField(
        child=rest_framework.serializers.IntegerField(), source="blacklist_publisher_groups", required=False
    )


class CampaignTargetingSerializer(restapi.serializers.base.RESTAPIBaseSerializer):
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

    devices = restapi.serializers.targeting.DevicesSerializer(source="target_devices", required=False)
    environments = restapi.serializers.targeting.EnvironmentsSerializer(source="target_environments", required=False)
    os = restapi.serializers.targeting.OSsSerializer(source="target_os", required=False)
    publisher_groups = PublisherGroupsSerializer(source="*", required=False)


class CampaignSerializer(
    restapi.serializers.serializers.PermissionedFieldsMixin, restapi.serializers.base.RESTAPIBaseSerializer
):
    class Meta:
        permissioned_fields = {"frequency_capping": "zemauth.can_set_frequency_capping"}

    id = restapi.serializers.fields.IdField(read_only=True, source="campaign.id")
    account_id = restapi.serializers.fields.IdField(source="campaign.account_id")
    name = restapi.serializers.fields.PlainCharField(
        max_length=256, error_messages={"required": "Please specify campaign name."}
    )
    iab_category = restapi.serializers.fields.DashConstantField(constants.IABCategory, required=False)
    language = restapi.serializers.fields.DashConstantField(constants.Language, required=False)
    type = restapi.serializers.fields.DashConstantField(
        constants.CampaignType, default=constants.CampaignType.CONTENT, required=False, source="campaign.type"
    )
    archived = rest_framework.serializers.BooleanField(required=False)
    autopilot = rest_framework.serializers.BooleanField(required=False)
    tracking = CampaignTrackingSerializer(source="*", required=False)
    targeting = CampaignTargetingSerializer(source="*", required=False)
    frequency_capping = restapi.serializers.fields.BlankIntegerField(allow_null=True, required=False)

    def validate_iab_category(self, value):
        if value != constants.IABCategory.IAB24 and "-" not in value:
            raise rest_framework.serializers.ValidationError(
                "Tier 1 IAB categories not allowed, please use Tier 2 IAB categories."
            )
        return value


class CampaignIdsSerializer(restapi.serializers.base.RESTAPIBaseSerializer):
    id = restapi.serializers.fields.IdField(read_only=True)


class CampaignQueryParams(
    restapi.serializers.serializers.QueryParamsExpectations, restapi.serializers.serializers.PaginationParametersMixin
):
    account_id = restapi.serializers.fields.IdField(required=False)
    only_ids = rest_framework.serializers.BooleanField(default=False, required=False)
    include_archived = rest_framework.serializers.BooleanField(required=False)
    exclude_inactive = rest_framework.serializers.BooleanField(default=False, required=False)
