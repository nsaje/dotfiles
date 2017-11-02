from rest_framework import serializers
from rest_framework_recursive.fields import RecursiveField

import restapi.fields


class BlueKaiCategorySerializer(serializers.Serializer):
    category_id = serializers.IntegerField()
    name = restapi.fields.PlainCharField()
    description = restapi.fields.PlainCharField()
    navigation_only = serializers.BooleanField()
    child_nodes = serializers.ListField(child=RecursiveField())
    reach = serializers.SerializerMethodField()
    price = serializers.DecimalField(max_digits=None, decimal_places=2)

    def get_reach(self, data):
        return data['reach']['value']


class BlueKaiReachSerializer(serializers.Serializer):
    value = serializers.IntegerField()
    relative = serializers.IntegerField()


class BlueKaiCategoryInternalSerializer(BlueKaiCategorySerializer):
    reach = BlueKaiReachSerializer()
