import decimal

import rest_framework.serializers

import dash.constants
import restapi.access
import restapi.credit.v1.serializers
import restapi.serializers.base
import restapi.serializers.fields
import restapi.serializers.serializers


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
    account_id = restapi.serializers.fields.IdField(allow_null=True, required=False)

    start_date = rest_framework.serializers.DateField()
    end_date = rest_framework.serializers.DateField(allow_null=True)

    license_fee = restapi.serializers.fields.PercentToDecimalField(
        max_digits=5, decimal_places=4, rounding=decimal.ROUND_HALF_DOWN
    )

    flat_fee = rest_framework.serializers.DecimalField(
        source="get_flat_fee", max_digits=20, decimal_places=4, read_only=True, rounding=decimal.ROUND_HALF_DOWN
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
            restapi.access.get_agency(self.context["request"].user, agency_id) if agency_id is not None else None
        )

        account_id = value.get("account_id")
        value["account"] = (
            restapi.access.get_account(self.context["request"].user, account_id) if account_id is not None else None
        )

        return value


class CreditQueryParams(restapi.serializers.serializers.QueryParamsExpectations):
    agency_id = restapi.serializers.fields.IdField(required=False)
    account_id = restapi.serializers.fields.IdField(required=False)
    active = restapi.serializers.fields.NullBooleanField(required=False)
    offset = restapi.serializers.fields.IntegerField(required=False)
    limit = restapi.serializers.fields.IntegerField(required=False)
