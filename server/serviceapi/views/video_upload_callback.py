from django.conf import settings
from rest_framework import serializers

import dash.features.videoassets.models
import restapi.fields

from .. import base
from .. import authentication


SERVICE_NAME = 'l1-video-upload'


class PutSerializer(serializers.Serializer):
    status = restapi.fields.DashConstantField(dash.features.videoassets.constants.VideoAssetStatus)


class VideoUploadCallbackView(base.ServiceAPIBaseView):
    authentication_classes = (
        authentication.gen_service_authentication(SERVICE_NAME, settings.LAMBDA_VIDEO_UPLOAD_SIGN_KEY),)

    def put(self, request, videoasset_id):
        serializer = PutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        videoasset = dash.features.videoassets.models.VideoAsset.objects.get(pk=videoasset_id)
        videoasset.set_status(serializer.validated_data['status'])

        return self.response_ok('ok')
