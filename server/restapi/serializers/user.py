import rest_framework.serializers

import restapi.serializers.base
import restapi.serializers.fields


class UserSerializer(restapi.serializers.base.RESTAPIBaseSerializer):
    id = restapi.serializers.fields.IdField(required=False)
    name = rest_framework.serializers.CharField(required=False)
