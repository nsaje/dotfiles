import decimal

import rest_framework.serializers

import restapi.campaignbudget.v1.serializers
import restapi.serializers.fields
import restapi.serializers.serializers


class CampaignBudgetSerializer(
    restapi.serializers.serializers.PermissionedFieldsMixin,
    restapi.campaignbudget.v1.serializers.CampaignBudgetSerializer,
):
    class Meta:
        permissioned_fields = {
            "license_fee": "zemauth.can_view_platform_cost_breakdown",
            "margin": "zemauth.can_manage_agency_margin",
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
    total = rest_framework.serializers.DecimalField(
        source="allocated_amount", max_digits=20, decimal_places=4, read_only=True, rounding=decimal.ROUND_HALF_DOWN
    )
    campaign_name = restapi.serializers.fields.PlainCharField(source="campaign.name", read_only=True)
