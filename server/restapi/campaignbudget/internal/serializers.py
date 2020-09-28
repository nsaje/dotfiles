import decimal

import rest_framework.serializers

import restapi.campaignbudget.v1.serializers
import restapi.serializers.fields
import restapi.serializers.serializers
import zemauth.access
from zemauth.features.entity_permission import Permission


class CampaignBudgetSerializer(restapi.campaignbudget.v1.serializers.CampaignBudgetSerializer):
    class Meta(restapi.campaignbudget.v1.serializers.CampaignBudgetSerializer.Meta):
        entity_permissioned_fields = {
            "config": {
                "entity_id_getter_fn": lambda data: data.get("credit_id"),
                "entity_access_fn": zemauth.access.get_credit_line_item,
            },
            "fields": {
                "margin": Permission.AGENCY_SPEND_MARGIN,
                "license_fee": Permission.MEDIA_COST_DATA_COST_LICENCE_FEE,
                "service_fee": Permission.BASE_COSTS_SERVICE_FEE,
            },
        }

    id = restapi.serializers.fields.IdField(required=False, allow_null=True)
    comment = restapi.serializers.fields.PlainCharField(
        required=False, max_length=256, allow_null=True, allow_blank=True
    )
    can_edit_start_date = rest_framework.serializers.BooleanField(read_only=True)
    can_edit_end_date = rest_framework.serializers.BooleanField(read_only=True)
    can_edit_amount = rest_framework.serializers.BooleanField(read_only=True)
    created_by = rest_framework.serializers.EmailField(read_only=True)
    created_dt = rest_framework.serializers.DateTimeField(read_only=True)
    margin = restapi.serializers.fields.PercentToDecimalField(
        max_digits=5, decimal_places=4, rounding=decimal.ROUND_HALF_DOWN
    )
    license_fee = restapi.serializers.fields.PercentToDecimalField(
        source="credit.license_fee",
        decimal_places=4,
        max_digits=5,
        required=False,
        rounding=decimal.ROUND_HALF_DOWN,
        read_only=True,
    )
    service_fee = restapi.serializers.fields.PercentToDecimalField(
        source="credit.service_fee",
        decimal_places=4,
        max_digits=5,
        required=False,
        rounding=decimal.ROUND_HALF_DOWN,
        read_only=True,
    )
    allocated_amount = rest_framework.serializers.DecimalField(
        max_digits=20, decimal_places=4, read_only=True, rounding=decimal.ROUND_HALF_DOWN
    )
    campaign_name = restapi.serializers.fields.PlainCharField(source="campaign.name", read_only=True)
