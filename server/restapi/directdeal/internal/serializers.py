import decimal
from collections import OrderedDict

import rest_framework.serializers

import restapi.serializers.base
import restapi.serializers.fields
import restapi.serializers.serializers
import utils.exc
import zemauth
from zemauth.features.entity_permission import Permission


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


class DirectDealSerializer(
    restapi.serializers.serializers.EntityPermissionedFieldsMixin, restapi.serializers.base.RESTAPIBaseSerializer
):
    class Meta:
        entity_permissioned_fields = {
            "config": {
                "entity_id_getter_fn": lambda data: data.get("id"),
                "entity_access_fn": zemauth.access.get_direct_deal,
            },
            "fields": {"deal_id": Permission.READ},
        }

    id = restapi.serializers.fields.IdField(required=False, allow_null=True)
    deal_id = rest_framework.serializers.CharField(max_length=100, allow_null=False, allow_blank=False)
    agency_id = restapi.serializers.fields.IdField(allow_null=True, required=False)
    agency_name = rest_framework.serializers.CharField(source="agency.name", default=None, read_only=True)
    account_id = restapi.serializers.fields.IdField(allow_null=True, required=False)
    account_name = rest_framework.serializers.CharField(source="account.settings.name", default=None, read_only=True)
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

    def has_entity_permission(
        self, user: zemauth.models.User, permission: Permission, config: OrderedDict, data: OrderedDict
    ) -> bool:
        id = data.get("id")
        if id is not None:
            return super().has_entity_permission(user, permission, config, data)

        agency_id = data.get("agency_id")
        if agency_id is not None:
            try:
                zemauth.access.get_agency(user, permission, agency_id)
                return True
            except utils.exc.MissingDataError:
                return False
        account_id = data.get("account_id")
        if account_id is not None:
            try:
                zemauth.access.get_account(user, permission, account_id)
                return True
            except utils.exc.MissingDataError:
                return False
        return False


class DirectDealQueryParams(
    restapi.serializers.serializers.QueryParamsExpectations, restapi.serializers.serializers.PaginationParametersMixin
):
    campaign_id = restapi.serializers.fields.IdField(required=False)
    agency_id = restapi.serializers.fields.IdField(required=False)
    account_id = restapi.serializers.fields.IdField(required=False)
    agency_only = restapi.serializers.fields.NullBooleanField(required=False)
    keyword = restapi.serializers.fields.PlainCharField(required=False)
