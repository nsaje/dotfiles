import decimal
from collections import OrderedDict

import rest_framework.serializers

import core.features.delivery_status
import dash.constants
import restapi.adgroup.v1.serializers
import restapi.directdeal.internal.serializers
import restapi.serializers.base
import restapi.serializers.bid_modifiers
import restapi.serializers.deals
import restapi.serializers.fields
import restapi.serializers.hack
import restapi.serializers.serializers
import restapi.serializers.targeting
import utils.exc
import zemauth
from zemauth.features.entity_permission import Permission


class CloneAdGroupSerializer(restapi.serializers.base.RESTAPIBaseSerializer):
    ad_group_id = restapi.serializers.fields.IdField(required=True)
    destination_campaign_id = restapi.serializers.fields.IdField(
        required=True,
        error_messages={"required": "Please select destination campaign", "null": "Please select destination campaign"},
    )
    destination_ad_group_name = restapi.serializers.fields.PlainCharField(
        required=True,
        error_messages={
            "required": "Please provide a name for destination ad group",
            "blank": "Please provide a name for destination ad group",
        },
        max_length=256,
    )
    clone_ads = rest_framework.serializers.BooleanField()


class CloneAdGroupResponseSerializer(restapi.serializers.base.RESTAPIBaseSerializer):
    id = restapi.serializers.fields.IdField()
    campaign_id = restapi.serializers.fields.IdField()
    name = rest_framework.serializers.CharField(read_only=True)

    state = restapi.serializers.fields.DashConstantField(dash.constants.AdGroupSettingsState)
    status = restapi.serializers.fields.DashConstantField(dash.constants.AdGroupRunningStatus)
    active = restapi.serializers.fields.DashConstantField(core.features.delivery_status.DetailedDeliveryStatus)


class ExtraDataDefaultSettingsSerializer(restapi.serializers.base.RESTAPIBaseSerializer):
    target_regions = restapi.serializers.targeting.TargetRegionsSerializer(required=False, allow_null=True)
    exclusion_target_regions = restapi.serializers.targeting.TargetRegionsSerializer(required=False, allow_null=True)
    target_devices = restapi.serializers.targeting.DevicesSerializer(required=False, allow_null=True)
    target_os = restapi.serializers.targeting.OSsSerializer(required=False, allow_null=True)
    target_environments = restapi.serializers.targeting.EnvironmentsSerializer(required=False, allow_null=True)


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


class ExtraDataCurrentBidsSerializer(restapi.serializers.base.RESTAPIBaseSerializer):
    cpc = restapi.serializers.fields.TwoWayBlankDecimalField(
        max_digits=10, decimal_places=4, allow_null=False, required=True, rounding=decimal.ROUND_HALF_DOWN
    )
    cpm = restapi.serializers.fields.TwoWayBlankDecimalField(
        max_digits=10, decimal_places=4, allow_null=False, required=True, rounding=decimal.ROUND_HALF_DOWN
    )


class ExtraDataSerializer(restapi.serializers.base.RESTAPIBaseSerializer):
    action_is_waiting = rest_framework.serializers.BooleanField(default=False, required=False)
    can_restore = rest_framework.serializers.BooleanField(default=False, required=False)
    is_campaign_autopilot_enabled = rest_framework.serializers.BooleanField(default=False, required=False)
    account_id = restapi.serializers.fields.IdField(required=False)
    agency_id = restapi.serializers.fields.IdField(required=False)
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
    bid_modifier_type_summaries = rest_framework.serializers.ListField(
        child=restapi.serializers.bid_modifiers.BidModifierTypeSummary(), required=False
    )
    current_bids = ExtraDataCurrentBidsSerializer(read_only=True)
    agency_uses_realtime_autopilot = rest_framework.serializers.BooleanField(read_only=True, default=False)


class AdGroupAutopilotSerializer(restapi.serializers.base.RESTAPIBaseSerializer):
    state = restapi.serializers.fields.DashConstantField(
        dash.constants.AdGroupSettingsAutopilotState, source="autopilot_state", required=False
    )
    max_bid = restapi.serializers.fields.TwoWayBlankDecimalField(
        source="local_max_autopilot_bid",
        max_digits=10,
        decimal_places=4,
        allow_null=True,
        required=False,
        rounding=decimal.ROUND_HALF_DOWN,
    )


class AdGroupSerializer(
    restapi.serializers.serializers.EntityPermissionedFieldsMixin, restapi.adgroup.v1.serializers.AdGroupSerializer
):
    class Meta(restapi.adgroup.v1.serializers.AdGroupSerializer.Meta):
        fields = (
            "id",
            "campaign_id",
            "name",
            "bidding_type",
            "bid",
            "daily_budget",
            "state",
            "archived",
            "start_date",
            "end_date",
            "tracking_code",
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
            "click_capping_daily_click_budget": "zemauth.can_set_click_capping_daily_click_budget",
            "additional_data": "zemauth.can_use_ad_additional_data",
        }
        entity_permissioned_fields = {
            "config": {
                "entity_id_getter_fn": lambda data: data.get("id"),
                "entity_access_fn": zemauth.access.get_ad_group,
            },
            # Seeing deals requires write permission
            "fields": {"deals": Permission.WRITE},
        }

    manage_rtb_sources_as_one = rest_framework.serializers.BooleanField(source="b1_sources_group_enabled")
    notes = rest_framework.serializers.CharField(read_only=True)
    autopilot = AdGroupAutopilotSerializer(source="*", required=False)
    deals = rest_framework.serializers.ListSerializer(
        child=restapi.directdeal.internal.serializers.DirectDealSerializer(), default=[], allow_empty=True
    )
    bid = restapi.serializers.fields.TwoWayBlankDecimalField(
        source="local_bid",
        max_digits=10,
        decimal_places=4,
        allow_null=True,
        required=False,
        rounding=decimal.ROUND_HALF_DOWN,
    )

    def has_entity_permission(
        self, user: zemauth.models.User, permission: Permission, config: OrderedDict, data: OrderedDict
    ) -> bool:
        ad_group_id = data.get("id")
        if ad_group_id is not None:
            return super().has_entity_permission(user, permission, config, data)

        campaign_id = data.get("campaign_id")
        if campaign_id is not None:
            try:
                zemauth.access.get_campaign(user, permission, campaign_id)
                return True
            except utils.exc.MissingDataError:
                return False
        return False


class AdGroupInternalQueryParams(
    restapi.serializers.serializers.QueryParamsExpectations, restapi.serializers.serializers.PaginationParametersMixin
):
    campaign_id = restapi.serializers.fields.IdField(required=True)


class AdGroupListQueryParams(
    restapi.serializers.serializers.QueryParamsExpectations, restapi.serializers.serializers.PaginationParametersMixin
):
    agency_id = restapi.serializers.fields.IdField(required=False)
    account_id = restapi.serializers.fields.IdField(required=False)
    keyword = restapi.serializers.fields.PlainCharField(required=False)
