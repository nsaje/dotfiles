import rest_framework.serializers

import restapi.accountcredit.v1.serializers
import restapi.serializers.fields


class AccountCreditSerializer(restapi.accountcredit.v1.serializers.AccountCreditSerializer):
    class Meta(restapi.accountcredit.v1.serializers.AccountCreditSerializer.Meta):
        pass

    comment = restapi.serializers.fields.PlainCharField(read_only=True, max_length=256)
    is_available = rest_framework.serializers.BooleanField(read_only=True)
    is_agency = rest_framework.serializers.BooleanField(read_only=True)
