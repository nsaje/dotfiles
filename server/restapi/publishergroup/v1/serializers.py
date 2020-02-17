import rest_framework.serializers

import core.features.publisher_groups
import restapi.access
import restapi.serializers.fields
from restapi.serializers import serializers


class PublisherGroupSerializer(serializers.DataNodeSerializerMixin, rest_framework.serializers.ModelSerializer):
    class Meta:
        model = core.features.publisher_groups.PublisherGroup
        fields = ("id", "name", "account_id")
        list_serializer_class = serializers.DataNodeListSerializer

    id = restapi.serializers.fields.IdField(read_only=True)
    name = restapi.serializers.fields.PlainCharField(max_length=127)
    account_id = restapi.serializers.fields.IdField(read_only=True)

    def create(self, validated_data):
        return core.features.publisher_groups.PublisherGroup.objects.create(
            validated_data["request"],
            name=validated_data["name"],
            account=restapi.access.get_account(validated_data["request"].user, validated_data["account_id"]),
        )

    def update(self, instance, validated_data):
        instance.name = validated_data.get("name", instance.name)
        instance.save(validated_data["request"])
        return instance
