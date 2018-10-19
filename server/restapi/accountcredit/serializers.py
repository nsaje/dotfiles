import decimal

import rest_framework.serializers

import restapi.serializers.fields
import restapi.serializers.serializers


class AccountCreditSerializer(
    restapi.serializers.serializers.PermissionedFieldsMixin, rest_framework.serializers.Serializer
):
    class Meta:
        permissioned_fields = {"license_fee": "zemauth.can_view_platform_cost_breakdown"}

    id = restapi.serializers.fields.IdField(read_only=True)
    created_on = rest_framework.serializers.DateField(source="get_creation_date", read_only=True)
    start_date = rest_framework.serializers.DateField(read_only=True)
    end_date = rest_framework.serializers.DateField(read_only=True, allow_null=True)
    total = rest_framework.serializers.DecimalField(
        source="effective_amount", max_digits=20, decimal_places=4, read_only=True, rounding=decimal.ROUND_HALF_DOWN
    )
    allocated = rest_framework.serializers.DecimalField(
        source="get_allocated_amount", max_digits=20, decimal_places=4, read_only=True, rounding=decimal.ROUND_HALF_DOWN
    )
    available = rest_framework.serializers.DecimalField(
        source="get_available_amount", max_digits=20, decimal_places=4, read_only=True, rounding=decimal.ROUND_HALF_DOWN
    )
    license_fee = rest_framework.serializers.DecimalField(
        max_digits=5, decimal_places=4, read_only=True, rounding=decimal.ROUND_HALF_DOWN
    )
