from django.db.models import Q
from rest_framework import serializers

from dash import constants

import core.entity

import restapi.access
import restapi.fields


class CloneContentAdsSerializer(serializers.Serializer):
    ad_group_id = restapi.fields.IdField()
    batch_id = restapi.fields.IdField(required=False)
    content_ad_ids = restapi.fields.CommaListField(
        child=restapi.fields.IdField())

    destination_ad_group_id = restapi.fields.IdField()

    def validate(self, data):
        if not data.get('batch_id') and not data.get('content_ad_ids'):
            # public endpoint does not allow select all
            raise serializers.ValidationError('Upload batch or content ads should be selected')
        return data


class CloneContentAdsInternalSerializer(CloneContentAdsSerializer):

    deselected_content_ad_ids = restapi.fields.CommaListField(
        child=restapi.fields.IdField())
    state = restapi.fields.DashConstantField(constants.ContentAdSourceState, required=False)

    def validate(self, data):
        return data


class UploadBatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = core.entity.UploadBatch
        fields = ('id', 'name', 'ad_group_id')

    id = restapi.fields.IdField()
    ad_group_id = restapi.fields.IdField()


def get_content_ads(objects, data):
    if data.get('not_selected_content_ad_ids'):
        objects = objects.exclude(id__in=data['not_selected_content_ad_ids'])

    batch_id = data.get('batch_id')
    content_ad_ids = data.get('content_ad_ids')

    if batch_id and content_ad_ids:
        objects = objects.filter(Q(batch_id=batch_id) | Q(id__in=content_ad_ids))
    elif batch_id:
        objects = objects.filter(batch_id=batch_id)
    elif content_ad_ids:
        objects = objects.filter(id__in=content_ad_ids)

    return objects
