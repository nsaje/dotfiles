import decimal

import rest_framework.serializers

import restapi.serializers.base
import restapi.serializers.fields
import restapi.serializers.serializers
import zemauth.access
from dash import constants
from zemauth.features.entity_permission import Permission


class CampaignBudgetSerializer(
    restapi.serializers.serializers.EntityPermissionedFieldsMixin,
    restapi.serializers.serializers.PermissionedFieldsMixin,
    restapi.serializers.base.RESTAPIBaseSerializer,
):
    class Meta:
        entity_permissioned_fields = {
            "config": {
                "entity_id_getter_fn": lambda data: data.get("credit_id"),
                "entity_access_fn": zemauth.access.get_credit_line_item,
            },
            "fields": {
                "margin": {
                    "permission": Permission.BUDGET_MARGIN,
                    "fallback_permission": "zemauth.can_manage_agency_margin",
                }
            },
        }

    id = restapi.serializers.fields.IdField(read_only=True)
    credit_id = restapi.serializers.fields.IdField(source="credit.id")
    start_date = rest_framework.serializers.DateField()
    end_date = rest_framework.serializers.DateField()
    amount = restapi.serializers.fields.TwoWayBlankDecimalField(
        max_digits=20, decimal_places=4, output_precision=0, rounding=decimal.ROUND_HALF_DOWN
    )
    margin = rest_framework.serializers.DecimalField(
        decimal_places=4, max_digits=5, required=False, rounding=decimal.ROUND_HALF_DOWN
    )
    comment = restapi.serializers.fields.PlainCharField(required=False, max_length=256)
    state = restapi.serializers.fields.DashConstantField(constants.BudgetLineItemState, read_only=True)
    spend = rest_framework.serializers.DecimalField(
        source="get_local_spend_data_bcm",
        max_digits=20,
        decimal_places=4,
        read_only=True,
        rounding=decimal.ROUND_HALF_DOWN,
    )
    available = rest_framework.serializers.DecimalField(
        source="get_local_available_data_bcm",
        max_digits=20,
        decimal_places=4,
        read_only=True,
        rounding=decimal.ROUND_HALF_DOWN,
    )
