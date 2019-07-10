import decimal

import rest_framework.serializers

import restapi.campaignbudget.v1.serializers


class CampaignBudgetSerializer(restapi.campaignbudget.v1.serializers.CampaignBudgetSerializer):

    can_edit_start_date = rest_framework.serializers.BooleanField(read_only=True)
    can_edit_end_date = rest_framework.serializers.BooleanField(read_only=True)
    can_edit_amount = rest_framework.serializers.BooleanField(read_only=True)
    created_by = rest_framework.serializers.EmailField(read_only=True)
    created_dt = rest_framework.serializers.DateTimeField(read_only=True)
    license_fee = rest_framework.serializers.DecimalField(
        source="credit.license_fee",
        decimal_places=4,
        max_digits=5,
        required=False,
        rounding=decimal.ROUND_HALF_DOWN,
        read_only=True,
    )
