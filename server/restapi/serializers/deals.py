import rest_framework.serializers

import restapi.serializers.base
import restapi.serializers.fields


# TODO (msuber): remove when refactor account/ campaign/ adgroup restapi with new deals schema
class DealSerializer(restapi.serializers.base.RESTAPIBaseSerializer):
    level = rest_framework.serializers.CharField(required=False)
    direct_deal_connection_id = restapi.serializers.fields.IdField(required=False)
    deal_id = rest_framework.serializers.CharField(required=False)
    source = rest_framework.serializers.CharField(required=False)
    exclusive = rest_framework.serializers.BooleanField(default=False, required=False)
    description = rest_framework.serializers.CharField(required=False)
    is_applied = rest_framework.serializers.BooleanField(default=False, required=False)
