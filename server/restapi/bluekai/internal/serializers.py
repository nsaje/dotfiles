from rest_framework import serializers

import restapi.bluekai.v1.serializers
import restapi.serializers.base


class BlueKaiReachSerializer(restapi.serializers.base.RESTAPIBaseSerializer):
    value = serializers.IntegerField()
    relative = serializers.IntegerField()


class BlueKaiCategoryInternalSerializer(restapi.bluekai.v1.serializers.BlueKaiCategorySerializer):
    reach = BlueKaiReachSerializer()
