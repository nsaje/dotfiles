from rest_framework import serializers
from rest_framework import fields

import restapi.fields
import restapi.serializers
import restapi.common.serializers

from . import models
from . import constants


DIRECT_UPLOAD = 'DIRECT_UPLOAD'
UPLOAD_TYPES = [DIRECT_UPLOAD]


class UploadInfoSerializer(serializers.Serializer):
    type = fields.ChoiceField(choices=UPLOAD_TYPES)
    url = restapi.fields.PlainCharField(required=False)


class VideoAssetSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.VideoAsset
        fields = ('id', 'account', 'status', 'status_message', 'error_code',
                  'error_message', 'name', 'upload', 'preview_url')
        read_only_fields = ('id', 'account', 'status',)

    account = restapi.fields.IdField()
    status = restapi.fields.DashConstantField(constants.VideoAssetStatus)
    status_message = fields.CharField(read_only=True, source='get_status_message')
    error_message = fields.CharField(read_only=True, source='get_error_message')
    preview_url = fields.CharField(read_only=True, source='get_preview_url')
    name = restapi.fields.PlainCharField()
    upload = UploadInfoSerializer(required=False)


class VideoAssetPostSerializer(serializers.Serializer):
    name = restapi.fields.PlainCharField()
    upload = UploadInfoSerializer()
