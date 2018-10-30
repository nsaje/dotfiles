from django.db.models import Q
from rest_framework import fields
from rest_framework import serializers

import core.models
import restapi.access
import restapi.serializers.fields
from dash import constants


class CloneContentAdsSerializer(serializers.Serializer):
    ad_group_id = restapi.serializers.fields.IdField()
    batch_id = restapi.serializers.fields.IdField(required=False, allow_null=True)
    content_ad_ids = fields.ListField(child=restapi.serializers.fields.IdField(), required=False)
    deselected_content_ad_ids = fields.ListField(child=restapi.serializers.fields.IdField(), required=False)

    destination_ad_group_id = restapi.serializers.fields.IdField(
        error_messages={"required": "Please select destination ad group", "null": "Please select destination ad group"}
    )
    destination_batch_name = restapi.serializers.fields.PlainCharField(
        required=True,
        error_messages={
            "required": "Please provide a name for destination upload batch",
            "blank": "Please provide a name for destination upload batch",
        },
    )
    state = restapi.serializers.fields.DashConstantField(
        constants.ContentAdSourceState, required=False, allow_null=True
    )


class AdGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = core.models.UploadBatch
        fields = ("id", "name")

    id = restapi.serializers.fields.IdField()
    name = restapi.serializers.fields.PlainCharField(max_length=1024)


class UploadBatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = core.models.UploadBatch
        fields = ("id", "name", "ad_group")

    id = restapi.serializers.fields.IdField()
    name = restapi.serializers.fields.PlainCharField(max_length=1024)
    ad_group = AdGroupSerializer()


def get_content_ads(objects, data):
    if data.get("deselected_content_ad_ids"):
        objects = objects.exclude(id__in=data["deselected_content_ad_ids"])

    batch_id = data.get("batch_id")
    content_ad_ids = data.get("content_ad_ids")

    if batch_id and content_ad_ids:
        objects = objects.filter(Q(batch_id=batch_id) | Q(id__in=content_ad_ids))
    elif batch_id:
        objects = objects.filter(batch_id=batch_id)
    elif content_ad_ids:
        objects = objects.filter(id__in=content_ad_ids)

    if not objects.exists():
        raise serializers.ValidationError("Please select at least one content ad to copy.")

    return objects
