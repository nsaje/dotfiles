import rest_framework.serializers

import restapi.serializers.fields


class AccountCreditSerializer(rest_framework.serializers.Serializer):
    id = restapi.serializers.fields.IdField(read_only=True)
    created_on = rest_framework.serializers.DateField(source="get_creation_date", read_only=True)
    start_date = rest_framework.serializers.DateField(read_only=True)
    end_date = rest_framework.serializers.DateField(read_only=True, allow_null=True)
    total = rest_framework.serializers.DecimalField(
        source="effective_amount", max_digits=20, decimal_places=4, read_only=True
    )
    allocated = rest_framework.serializers.DecimalField(
        source="get_allocated_amount", max_digits=20, decimal_places=4, read_only=True
    )
    available = rest_framework.serializers.DecimalField(
        source="get_available_amount", max_digits=20, decimal_places=4, read_only=True
    )
