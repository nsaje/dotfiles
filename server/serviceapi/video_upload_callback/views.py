from django.conf import settings
from rest_framework import serializers

import dash.features.videoassets.models
import restapi.serializers.fields

from .. import base
from utils.rest_common import authentication


SERVICE_NAME = "l1-video-upload"


class FormatSerializer(serializers.Serializer):
    width = serializers.IntegerField()
    height = serializers.IntegerField()
    bitrate = serializers.IntegerField()
    mime = restapi.serializers.fields.PlainCharField()
    filename = restapi.serializers.fields.PlainCharField()


class PutSerializer(serializers.ModelSerializer):
    class Meta:
        model = dash.features.videoassets.models.VideoAsset
        fields = ("status", "error_code", "duration", "formats")

    status = restapi.serializers.fields.DashConstantField(dash.features.videoassets.constants.VideoAssetStatus)
    formats = FormatSerializer(many=True, required=False)


class VideoUploadCallbackView(base.ServiceAPIBaseView):
    authentication_classes = (
        authentication.gen_service_authentication(SERVICE_NAME, settings.LAMBDA_VIDEO_UPLOAD_SIGN_KEY),
    )

    def put(self, request, videoasset_id):
        serializer = PutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        videoasset = dash.features.videoassets.models.VideoAsset.objects.get(pk=videoasset_id)
        videoasset.update_progress(
            status=serializer.validated_data["status"],
            error_code=serializer.validated_data.get("error_code"),
            duration=serializer.validated_data.get("duration"),
            formats=serializer.validated_data.get("formats"),
        )

        return self.response_ok("ok")
