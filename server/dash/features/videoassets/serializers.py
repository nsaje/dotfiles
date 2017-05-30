from rest_framework import serializers
from rest_framework import fields

import restapi.fields
import restapi.serializers
import restapi.common.serializers

import models
import constants


DIRECT_UPLOAD = 'DIRECT_UPLOAD'
UPLOAD_TYPES = [DIRECT_UPLOAD]


class UploadInfoSerializer(serializers.Serializer):
    type = fields.ChoiceField(choices=UPLOAD_TYPES)
    url = fields.CharField(required=False)


class VideoAssetSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.VideoAsset
        fields = ('id', 'account', 'status', 'status_message', 'name', 'upload')
        read_only_fields = ('id', 'account', 'status', 'status_message',)

    account = restapi.fields.IdField()
    status = restapi.fields.DashConstantField(constants.VideoAssetStatus)
    status_message = fields.CharField(read_only=True, source='get_status_message')
    name = fields.CharField()
    upload = UploadInfoSerializer(required=False)


class VideoAssetPostSerializer(serializers.Serializer):
    name = fields.CharField()
    upload = UploadInfoSerializer()
