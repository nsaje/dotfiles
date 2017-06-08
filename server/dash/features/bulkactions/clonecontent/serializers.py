from django.db.models import Q
from rest_framework import serializers
from rest_framework import fields

from dash import constants

import core.entity

import restapi.access
import restapi.fields


class CloneContentAdsSerializer(serializers.Serializer):
    ad_group_id = restapi.fields.IdField()
    batch_id = restapi.fields.IdField(required=False, allow_null=True)
    content_ad_ids = fields.ListField(child=restapi.fields.IdField(), required=False)

    destination_ad_group_id = restapi.fields.IdField()

    def validate(self, data):
        if not data.get('batch_id') and not data.get('content_ad_ids'):
            # public endpoint does not allow select all
            raise serializers.ValidationError('Upload batch or content ads should be selected')
        return data


class CloneContentAdsInternalSerializer(CloneContentAdsSerializer):

    deselected_content_ad_ids = fields.ListField(child=restapi.fields.IdField(), required=False)
    state = restapi.fields.DashConstantField(constants.ContentAdSourceState, required=False, allow_null=True)

    def validate(self, data):
        return data


class UploadBatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = core.entity.UploadBatch
        fields = ('id', 'name', 'ad_group_id')

    id = restapi.fields.IdField()
    ad_group_id = restapi.fields.IdField()


class AdGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = core.entity.UploadBatch
        fields = ('id', 'name')

    id = restapi.fields.IdField()


class UploadBatchInternalSerializer(serializers.ModelSerializer):
    class Meta:
        model = core.entity.UploadBatch
        fields = ('id', 'name', 'ad_group')

    id = restapi.fields.IdField()
    ad_group = AdGroupSerializer()


def get_content_ads(objects, data):
    if data.get('deselected_content_ad_ids'):
        objects = objects.exclude(id__in=data['deselected_content_ad_ids'])

    batch_id = data.get('batch_id')
    content_ad_ids = data.get('content_ad_ids')

    if batch_id and content_ad_ids:
        objects = objects.filter(Q(batch_id=batch_id) | Q(id__in=content_ad_ids))
    elif batch_id:
        objects = objects.filter(batch_id=batch_id)
    elif content_ad_ids:
        objects = objects.filter(id__in=content_ad_ids)

    return objects
