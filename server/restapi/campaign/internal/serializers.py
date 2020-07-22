import decimal

import rest_framework.serializers

import dash.constants
import restapi.campaign.v1.serializers
import restapi.campaignbudget.internal.serializers
import restapi.campaigngoal.v1.serializers
import restapi.credit.internal.serializers
import restapi.directdeal.internal.serializers
import restapi.serializers.base
import restapi.serializers.deals
import restapi.serializers.fields
import restapi.serializers.hack
import restapi.serializers.serializers
import restapi.serializers.user
import zemauth.access
import zemauth.models


class ExtraDataBudgetsOverviewSerializer(restapi.serializers.base.RESTAPIBaseSerializer):
    available_budgets_sum = rest_framework.serializers.DecimalField(
        max_digits=20, decimal_places=4, read_only=True, rounding=decimal.ROUND_HALF_DOWN
    )
    unallocated_credit = rest_framework.serializers.DecimalField(
        max_digits=20, decimal_places=4, read_only=True, rounding=decimal.ROUND_HALF_DOWN
    )
    campaign_spend = rest_framework.serializers.DecimalField(
        max_digits=20, decimal_places=4, read_only=True, rounding=decimal.ROUND_HALF_DOWN
    )
    base_media_spend = rest_framework.serializers.DecimalField(
        max_digits=20, decimal_places=4, read_only=True, rounding=decimal.ROUND_HALF_DOWN
    )
    base_data_spend = rest_framework.serializers.DecimalField(
        max_digits=20, decimal_places=4, read_only=True, rounding=decimal.ROUND_HALF_DOWN
    )
    media_spend = rest_framework.serializers.DecimalField(
        max_digits=20, decimal_places=4, read_only=True, rounding=decimal.ROUND_HALF_DOWN
    )
    data_spend = rest_framework.serializers.DecimalField(
        max_digits=20, decimal_places=4, read_only=True, rounding=decimal.ROUND_HALF_DOWN
    )
    service_fee = rest_framework.serializers.DecimalField(
        max_digits=20, decimal_places=4, read_only=True, rounding=decimal.ROUND_HALF_DOWN
    )
    license_fee = rest_framework.serializers.DecimalField(
        max_digits=20, decimal_places=4, read_only=True, rounding=decimal.ROUND_HALF_DOWN
    )
    margin = rest_framework.serializers.DecimalField(
        max_digits=20, decimal_places=4, read_only=True, rounding=decimal.ROUND_HALF_DOWN
    )


class CreditSerializer(restapi.credit.internal.serializers.CreditSerializer):
    def __init__(self, *args, **kwargs):
        super(CreditSerializer, self).__init__(*args, **kwargs)
        self.fields.pop("flat_fee")
        self.fields.pop("num_of_budgets")


class CampaignBudgetSerializer(restapi.campaignbudget.internal.serializers.CampaignBudgetSerializer):
    def __init__(self, *args, **kwargs):
        super(CampaignBudgetSerializer, self).__init__(*args, **kwargs)
        self.fields.pop("allocated_amount")
        self.fields.pop("campaign_name")


class ExtraDataSerializer(restapi.serializers.base.RESTAPIBaseSerializer):
    archived = rest_framework.serializers.BooleanField(default=False, required=False)
    language = restapi.serializers.fields.DashConstantField(dash.constants.Language, required=False)
    can_restore = rest_framework.serializers.BooleanField(default=False, required=False)
    agency_id = restapi.serializers.fields.IdField(required=False)
    currency = restapi.serializers.fields.DashConstantField(
        dash.constants.Currency, default=dash.constants.Currency.USD, required=False
    )
    goals_defaults = restapi.campaigngoal.v1.serializers.CampaignGoalsDefaultsSerializer()
    campaign_managers = rest_framework.serializers.ListField(
        child=restapi.serializers.user.UserSerializer(), default=[], allow_empty=True
    )
    hacks = rest_framework.serializers.ListField(
        child=restapi.serializers.hack.HackSerializer(), default=[], allow_empty=True
    )
    deals = rest_framework.serializers.ListField(
        child=restapi.serializers.deals.DealSerializer(), default=[], allow_empty=True
    )
    budgets_overview = ExtraDataBudgetsOverviewSerializer(required=False)
    budgets_depleted = rest_framework.serializers.ListSerializer(
        child=CampaignBudgetSerializer(), default=[], allow_empty=True
    )
    credits = rest_framework.serializers.ListSerializer(child=CreditSerializer(), default=[], allow_empty=True)


class CampaignSerializer(restapi.campaign.v1.serializers.CampaignSerializer):
    class Meta:
        permissioned_fields = {
            "frequency_capping": "zemauth.can_set_frequency_capping",
            "iab_category": "zemauth.can_modify_campaign_iab_category",
            "campaign_manager": "zemauth.can_modify_campaign_manager",
            "goals": "zemauth.can_see_campaign_goals",
            "deals": "zemauth.can_see_direct_deals_section",
        }

    campaign_manager = restapi.serializers.fields.IdField(required=False)
    goals = rest_framework.serializers.ListSerializer(
        child=restapi.campaigngoal.v1.serializers.CampaignGoalSerializer(), default=[], allow_empty=True
    )
    budgets = rest_framework.serializers.ListSerializer(child=CampaignBudgetSerializer(), default=[], allow_empty=True)
    deals = rest_framework.serializers.ListSerializer(
        child=restapi.directdeal.internal.serializers.DirectDealSerializer(), default=[], allow_empty=True
    )

    def validate_campaign_manager(self, value):
        if value is None:
            return value
        if not zemauth.models.User.objects.filter(pk=value).exists():
            raise rest_framework.serializers.ValidationError(["Invalid campaign manager."])
        return value

    def validate_iab_category(self, value):
        if value == dash.constants.IABCategory.IAB24:
            raise rest_framework.serializers.ValidationError(["Invalid IAB category."])
        return value

    def to_internal_value(self, data):
        value = super().to_internal_value(data)
        value["campaign_manager"] = self.to_internal_value_campaign_manager(data.get("campaign_manager"))
        return value

    def to_internal_value_campaign_manager(self, data):
        if data is None:
            return data
        return zemauth.models.User.objects.get(pk=data)


class CloneCampaignSerializer(restapi.serializers.base.RESTAPIBaseSerializer):
    destination_campaign_name = restapi.serializers.fields.PlainCharField(
        error_messages={
            "required": "Please provide a name for destination campaign",
            "blank": "Please provide a name for destination campaign",
        },
        max_length=127,
    )
    clone_ad_groups = rest_framework.serializers.BooleanField()
    clone_ads = rest_framework.serializers.BooleanField()
    ad_group_state_override = restapi.serializers.fields.DashConstantField(
        dash.constants.AdGroupSettingsState, required=False, allow_null=True
    )
    ad_state_override = restapi.serializers.fields.DashConstantField(
        dash.constants.ContentAdSourceState, required=False, allow_null=True
    )


class CampaignInternalQueryParams(
    restapi.serializers.serializers.QueryParamsExpectations, restapi.serializers.serializers.PaginationParametersMixin
):
    account_id = restapi.serializers.fields.IdField(required=True)


class CampaignListQueryParams(
    restapi.serializers.serializers.QueryParamsExpectations, restapi.serializers.serializers.PaginationParametersMixin
):
    agency_id = restapi.serializers.fields.IdField(required=False)
    account_id = restapi.serializers.fields.IdField(required=False)
    keyword = restapi.serializers.fields.PlainCharField(required=False)
