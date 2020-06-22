import decimal

import rest_framework.serializers

import dash.constants
import restapi.serializers.fields
import restapi.serializers.serializers
import zemauth.access
from zemauth.features.entity_permission import Permission


class CreditSerializer(
    restapi.serializers.serializers.EntityPermissionedFieldsMixin, rest_framework.serializers.Serializer
):
    class Meta:
        entity_permissioned_fields = {
            "config": {
                "entity_id_getter_fn": lambda data: data.get("id"),
                "entity_access_fn": zemauth.access.get_credit_line_item,
            },
            "fields": {
                "service_fee": {
                    "permission": Permission.BASE_COSTS_SERVICE_FEE,
                    "fallback_permission": "zemauth.can_see_service_fee",
                },
                "license_fee": {
                    "permission": Permission.MEDIA_COST_DATA_COST_LICENCE_FEE,
                    "fallback_permission": "zemauth.can_view_platform_cost_breakdown",
                },
            },
        }

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
    service_fee = rest_framework.serializers.DecimalField(
        max_digits=5, decimal_places=4, read_only=True, rounding=decimal.ROUND_HALF_DOWN
    )
    license_fee = rest_framework.serializers.DecimalField(
        max_digits=5, decimal_places=4, read_only=True, rounding=decimal.ROUND_HALF_DOWN
    )
    status = restapi.serializers.fields.DashConstantField(dash.constants.CreditLineItemStatus, read_only=True)
    currency = restapi.serializers.fields.DashConstantField(
        dash.constants.Currency, default=dash.constants.Currency.USD, required=False
    )
