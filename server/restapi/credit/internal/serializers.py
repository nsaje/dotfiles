import decimal
from collections import OrderedDict

import rest_framework.serializers

import dash.constants
import restapi.credit.v1.serializers
import restapi.serializers.base
import restapi.serializers.fields
import restapi.serializers.serializers
import utils.exc
import zemauth.access
import zemauth.models
from zemauth.features.entity_permission import Permission


class CreditTotalsSerializer(restapi.serializers.base.RESTAPIBaseSerializer):
    total = rest_framework.serializers.DecimalField(
        max_digits=20, decimal_places=4, read_only=True, rounding=decimal.ROUND_HALF_DOWN
    )
    allocated = rest_framework.serializers.DecimalField(
        max_digits=20, decimal_places=4, read_only=True, rounding=decimal.ROUND_HALF_DOWN
    )
    past = rest_framework.serializers.DecimalField(
        max_digits=20, decimal_places=4, read_only=True, rounding=decimal.ROUND_HALF_DOWN
    )
    available = rest_framework.serializers.DecimalField(
        max_digits=20, decimal_places=4, read_only=True, rounding=decimal.ROUND_HALF_DOWN
    )
    currency = restapi.serializers.fields.DashConstantField(
        dash.constants.Currency, default=dash.constants.Currency.USD, read_only=True
    )


class CreditSerializer(restapi.credit.v1.serializers.CreditSerializer):
    class Meta(restapi.credit.v1.serializers.CreditSerializer.Meta):
        pass

    created_by = rest_framework.serializers.EmailField(read_only=True)

    status = restapi.serializers.fields.DashConstantField(
        dash.constants.CreditLineItemStatus, default=dash.constants.CreditLineItemStatus.PENDING
    )
    currency = restapi.serializers.fields.DashConstantField(
        dash.constants.Currency, default=dash.constants.Currency.USD
    )

    agency_id = restapi.serializers.fields.IdField(allow_null=True, required=False)
    agency_name = rest_framework.serializers.CharField(source="agency.name", default=None, read_only=True)
    account_id = restapi.serializers.fields.IdField(allow_null=True, required=False)
    account_name = rest_framework.serializers.CharField(source="account.settings.name", default=None, read_only=True)

    start_date = rest_framework.serializers.DateField()
    end_date = rest_framework.serializers.DateField(allow_null=True)

    service_fee = restapi.serializers.fields.PercentToDecimalField(
        max_digits=5, decimal_places=4, rounding=decimal.ROUND_HALF_DOWN
    )
    license_fee = restapi.serializers.fields.PercentToDecimalField(
        max_digits=5, decimal_places=4, rounding=decimal.ROUND_HALF_DOWN
    )

    amount = rest_framework.serializers.IntegerField()

    contract_id = restapi.serializers.fields.PlainCharField(
        allow_null=True, allow_blank=True, required=False, max_length=256
    )
    contract_number = restapi.serializers.fields.PlainCharField(
        allow_null=True, allow_blank=True, required=False, max_length=256
    )

    comment = restapi.serializers.fields.PlainCharField(
        allow_null=True, allow_blank=True, required=False, max_length=256
    )

    salesforce_url = restapi.serializers.fields.PlainCharField(source="get_salesforce_url", read_only=True)

    is_available = rest_framework.serializers.BooleanField(read_only=True)

    num_of_budgets = rest_framework.serializers.IntegerField(read_only=True, source="get_number_of_budgets")

    def to_internal_value(self, data):
        value = super().to_internal_value(data)

        agency_id = value.get("agency_id")
        value["agency"] = (
            zemauth.access.get_agency(self.context["request"].user, Permission.WRITE, agency_id)
            if agency_id is not None
            else None
        )

        account_id = value.get("account_id")
        value["account"] = (
            zemauth.access.get_account(self.context["request"].user, Permission.WRITE, account_id)
            if account_id is not None
            else None
        )

        return value

    def has_entity_permission(
        self, user: zemauth.models.User, permission: Permission, config: OrderedDict, data: OrderedDict
    ) -> bool:
        credit_id = data.get("id")
        if credit_id is not None:
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


class CreditQueryParams(
    restapi.serializers.serializers.QueryParamsExpectations, restapi.serializers.serializers.PaginationParametersMixin
):
    agency_id = restapi.serializers.fields.IdField(required=False)
    account_id = restapi.serializers.fields.IdField(required=False)
    active = restapi.serializers.fields.NullBooleanField(required=False)
    exclude_canceled = restapi.serializers.fields.NullBooleanField(required=False)
