import rest_framework.serializers

import restapi.fields
import restapi.serializers

from dash import constants


class CampaignBudgetSerializer(rest_framework.serializers.Serializer):

    id = restapi.fields.IdField(read_only=True)
    credit_id = restapi.fields.IdField(
        source='credit.id',
    )
    start_date = rest_framework.serializers.DateField()
    end_date = rest_framework.serializers.DateField()
    amount = restapi.fields.TwoWayBlankDecimalField(
        max_digits=20,
        decimal_places=4,
        output_precision=0,
    )
    state = restapi.fields.DashConstantField(
        constants.BudgetLineItemState,
        read_only=True,
    )
    spend = rest_framework.serializers.DecimalField(
        source='get_local_spend_data_bcm',
        max_digits=20,
        decimal_places=4,
        read_only=True,
    )
    available = rest_framework.serializers.DecimalField(
        source='get_local_available_data_bcm',
        max_digits=20,
        decimal_places=4,
        read_only=True,
    )
