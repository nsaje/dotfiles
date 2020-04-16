import decimal

import rest_framework.serializers

import restapi.access
import restapi.serializers.base
import restapi.serializers.fields
import restapi.serializers.serializers


class CreditRefundSerializer(restapi.serializers.base.RESTAPIBaseSerializer):
    id = restapi.serializers.fields.IdField(read_only=True)
    account_id = restapi.serializers.fields.IdField(allow_null=False)
    credit_id = restapi.serializers.fields.IdField(source="credit.id", read_only=True)
    start_date = rest_framework.serializers.DateField()
    end_date = rest_framework.serializers.DateField(read_only=True)
    amount = rest_framework.serializers.IntegerField()
    effective_margin = restapi.serializers.fields.PercentToDecimalField(
        max_digits=5, decimal_places=4, rounding=decimal.ROUND_HALF_DOWN
    )
    comment = rest_framework.serializers.CharField()
    created_by = rest_framework.serializers.EmailField(read_only=True)
    created_dt = rest_framework.serializers.DateTimeField(read_only=True)

    def to_internal_value(self, data):
        value = super().to_internal_value(data)
        value["account"] = restapi.access.get_account(self.context["request"].user, value.get("account_id"))
        return value


class CreditRefundQueryParams(
    restapi.serializers.serializers.QueryParamsExpectations, restapi.serializers.serializers.PaginationParametersMixin
):
    agency_id = restapi.serializers.fields.IdField(required=False)
    account_id = restapi.serializers.fields.IdField(required=False)
