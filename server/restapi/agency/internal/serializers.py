import rest_framework.serializers

import restapi.serializers.base
import restapi.serializers.fields


class AgencySerializer(restapi.serializers.base.RESTAPIBaseSerializer):
    id = restapi.serializers.fields.IdField(read_only=True)
    name = rest_framework.serializers.CharField(max_length=127, required=False)
