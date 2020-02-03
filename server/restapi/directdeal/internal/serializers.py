import decimal

import rest_framework.serializers

import restapi.serializers.base
import restapi.serializers.fields


class DirectDealConnectionAccountSerializer(restapi.serializers.base.RESTAPIBaseSerializer):
    id = restapi.serializers.fields.IdField(read_only=True)
    name = rest_framework.serializers.CharField(source="settings.name", read_only=True)


class DirectDealConnectionCampaignSerializer(restapi.serializers.base.RESTAPIBaseSerializer):
    id = restapi.serializers.fields.IdField(read_only=True)
    name = rest_framework.serializers.CharField(source="settings.name", read_only=True)


class DirectDealConnectionAdGroupSerializer(restapi.serializers.base.RESTAPIBaseSerializer):
    id = restapi.serializers.fields.IdField(read_only=True)
    name = rest_framework.serializers.CharField(source="settings.ad_group_name", read_only=True)


class DirectDealConnectionSerializer(restapi.serializers.base.RESTAPIBaseSerializer):
    id = restapi.serializers.fields.IdField(read_only=True)
    account = DirectDealConnectionAccountSerializer(required=False)
    campaign = DirectDealConnectionCampaignSerializer(required=False)
    adgroup = DirectDealConnectionAdGroupSerializer(required=False)


class DirectDealSerializer(restapi.serializers.base.RESTAPIBaseSerializer):
    id = restapi.serializers.fields.IdField(required=False, allow_null=True)
    deal_id = rest_framework.serializers.CharField(max_length=100, allow_null=False, allow_blank=False)
    agency_id = restapi.serializers.fields.IdField(allow_null=True, required=False)
    account_id = restapi.serializers.fields.IdField(allow_null=True, required=False)
    description = rest_framework.serializers.CharField(allow_null=True, allow_blank=True, required=False)
    name = rest_framework.serializers.CharField(max_length=127, allow_null=False, allow_blank=False, required=True)
    source = restapi.serializers.fields.SourceIdSlugField(required=True, allow_null=False)
    floor_price = rest_framework.serializers.DecimalField(
        decimal_places=4, max_digits=10, required=False, allow_null=True, rounding=decimal.ROUND_HALF_DOWN
    )
    valid_from_date = rest_framework.serializers.DateField(allow_null=True, required=False)
    valid_to_date = rest_framework.serializers.DateField(allow_null=True, required=False)
    created_dt = rest_framework.serializers.DateTimeField(read_only=True)
    modified_dt = rest_framework.serializers.DateTimeField(read_only=True)
    created_by = rest_framework.serializers.EmailField(read_only=True)
    num_of_accounts = rest_framework.serializers.IntegerField(read_only=True, source="get_number_of_connected_accounts")
    num_of_campaigns = rest_framework.serializers.IntegerField(
        read_only=True, source="get_number_of_connected_campaigns"
    )
    num_of_adgroups = rest_framework.serializers.IntegerField(read_only=True, source="get_number_of_connected_adgroups")

    def to_internal_value(self, data):
        value = super().to_internal_value(data)

        agency_id = value.get("agency_id")
        if agency_id:
            value["agency"] = restapi.access.get_agency(self.context["request"].user, agency_id)

        account_id = value.get("account_id")
        if account_id:
            value["account"] = restapi.access.get_account(self.context["request"].user, account_id)

        return value
