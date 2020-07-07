from rest_framework import serializers

import core.models


class TagSerializer(serializers.BaseSerializer):
    class Meta:
        model = core.models.EntityTag
        fields = ("name",)

    def to_representation(self, instance):
        return instance.name

    def to_internal_value(self, data):
        return data
