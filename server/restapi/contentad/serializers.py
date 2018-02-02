import rest_framework.serializers

import dash.models
import dash.constants
import dash.features.contentupload
import restapi.fields


class ContentAdSerializer(rest_framework.serializers.ModelSerializer):

    class Meta:
        model = dash.models.ContentAd
        fields = ('id', 'ad_group_id', 'state', 'url', 'title', 'image_url', 'display_url', 'brand_name',
                  'description', 'call_to_action', 'label', 'image_crop', 'tracker_urls')
        read_only_fields = tuple(set(fields) - set(('state', 'url', 'tracker_urls', 'label')))

    id = restapi.fields.IdField(required=False)
    ad_group_id = restapi.fields.IdField(source='ad_group', required=False)
    state = restapi.fields.DashConstantField(dash.constants.ContentAdSourceState, required=False)
    url = rest_framework.serializers.URLField(required=False)
    image_url = rest_framework.serializers.URLField(source='get_image_url', required=False)


class ContentAdCandidateSerializer(rest_framework.serializers.ModelSerializer):

    class Meta:
        model = dash.models.ContentAdCandidate
        fields = ('url', 'title', 'image_url', 'display_url', 'brand_name',
                  'description', 'call_to_action', 'label', 'image_crop')
        extra_kwargs = {'primary_tracker_url': {'allow_empty': True}, 'secondary_tracker_url': {'allow_empty': True}}

    url = restapi.fields.PlainCharField(required=True)
    title = restapi.fields.PlainCharField(required=True)
    image_url = restapi.fields.PlainCharField(required=True)
    display_url = restapi.fields.PlainCharField(required=True)
    brand_name = restapi.fields.PlainCharField(required=True)
    description = restapi.fields.PlainCharField(required=True)
    call_to_action = restapi.fields.PlainCharField(required=True)
    image_crop = restapi.fields.PlainCharField(required=True)
    label = restapi.fields.PlainCharField(allow_blank=True, allow_null=True, required=False)

    def to_internal_value(self, external_data):
        internal_data = super(ContentAdCandidateSerializer, self).to_internal_value(external_data)
        tracker_urls = external_data.get('tracker_urls')
        if not tracker_urls:
            return internal_data
        if len(tracker_urls) > 0:
            internal_data['primary_tracker_url'] = tracker_urls[0]
        if len(tracker_urls) > 1:
            internal_data['secondary_tracker_url'] = tracker_urls[1]
        if len(tracker_urls) > 2:
            raise rest_framework.serializers.ValidationError('A maximum of two tracker URLs are supported.')
        return internal_data


class UploadBatchSerializer(rest_framework.serializers.Serializer):
    id = restapi.fields.IdField()
    status = restapi.fields.DashConstantField(dash.constants.UploadBatchStatus)
    approvedContentAds = ContentAdSerializer(many=True, source='get_approved_content_ads')

    def to_representation(self, batch):
        external_data = super(UploadBatchSerializer, self).to_representation(batch)
        cleaned_candidates = dash.features.contentupload.upload.get_candidates_with_errors(batch.contentadcandidate_set.all())
        external_data['validationStatus'] = [candidate['errors'] for candidate in cleaned_candidates]
        return external_data
