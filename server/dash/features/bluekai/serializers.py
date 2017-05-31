from rest_framework import serializers
from rest_framework_recursive.fields import RecursiveField


class BlueKaiCategorySerializer(serializers.Serializer):
    category_id = serializers.IntegerField()
    name = serializers.CharField()
    description = serializers.CharField()
    navigation_only = serializers.BooleanField()
    child_nodes = serializers.ListField(child=RecursiveField())
    reach = serializers.IntegerField()
    price = serializers.DecimalField(max_digits=None, decimal_places=2)
