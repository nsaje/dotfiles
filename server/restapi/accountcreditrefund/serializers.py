import rest_framework.serializers

import restapi.serializers.fields
import restapi.serializers.base


class AccountCreditRefundSerializer(restapi.serializers.base.RESTAPIBaseSerializer):
    id = restapi.serializers.fields.IdField(read_only=True)
    account_id = restapi.serializers.fields.IdField(source='account.id', read_only=True)
    credit_id = restapi.serializers.fields.IdField(source='credit.id', read_only=True)
    start_date = rest_framework.serializers.DateField()
    end_date = rest_framework.serializers.DateField(read_only=True)
    amount = rest_framework.serializers.IntegerField()
    comment = rest_framework.serializers.CharField(allow_blank=True, allow_null=True)
    created_by = rest_framework.serializers.EmailField(read_only=True)
    created_dt = rest_framework.serializers.DateTimeField(read_only=True)
