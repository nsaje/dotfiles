from rest_framework import fields
from rest_framework import serializers

import restapi.serializers.fields
from core.features.videoassets import constants
from core.features.videoassets import models


class UploadInfoSerializer(serializers.Serializer):
    type = restapi.serializers.fields.DashConstantField(constants.VideoAssetType)
    url = restapi.serializers.fields.PlainCharField(required=False)


class VideoAssetSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.VideoAsset
        fields = (
            "id",
            "account",
            "type",
            "status",
            "status_message",
            "error_code",
            "error_message",
            "name",
            "upload",
            "preview_url",
            "vast_url",
        )
        read_only_fields = ("id", "account", "status")

    account = restapi.serializers.fields.IdField()
    type = restapi.serializers.fields.DashConstantField(constants.VideoAssetType)
    status = restapi.serializers.fields.DashConstantField(constants.VideoAssetStatus)
    status_message = fields.CharField(read_only=True, source="get_status_message")
    error_message = fields.CharField(read_only=True, source="get_error_message")
    preview_url = fields.CharField(read_only=True, source="get_preview_url")
    name = restapi.serializers.fields.PlainCharField()
    upload = UploadInfoSerializer(required=False)
    vast_url = restapi.serializers.fields.PlainCharField(source="get_vast_url")


class VideoAssetPostSerializer(serializers.Serializer):
    name = restapi.serializers.fields.PlainCharField(required=False, allow_blank=True)
    vast_url = restapi.serializers.fields.PlainCharField(required=False, allow_blank=True)
    status = restapi.serializers.fields.DashConstantField(constants.VideoAssetStatus, required=False)
    upload = UploadInfoSerializer(required=False)
