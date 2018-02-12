import rest_framework.serializers
import rest_framework.permissions

import restapi.views
from . import serializers
from . import models
from . import service


class VideoAssetBaseView(restapi.views.RESTAPIBaseView):

    permission_classes = (rest_framework.permissions.IsAuthenticated,
                          restapi.access.HasAccountAccess,
                          restapi.access.gen_permission_class('zemauth.fea_video_upload'))


class VideoAssetListView(VideoAssetBaseView):

    def post(self, request, account_id):
        account = restapi.access.get_account(request.user, account_id)
        serializer = serializers.VideoAssetPostSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        if data['upload']['type'] == serializers.DIRECT_UPLOAD:
            video_asset, upload_info = service.initiate_asset_for_direct_upload(account, data['name'])
            video_asset.upload = upload_info
            return self.response_ok(serializers.VideoAssetSerializer(video_asset).data)
        else:
            return self.response_error("Unsupported upload type")


class VideoAssetView(VideoAssetBaseView):

    def get(self, request, account_id, videoasset_id):
        account = restapi.access.get_account(request.user, account_id)
        video_asset = models.VideoAsset.objects.get(account=account, id=videoasset_id)
        serializer = serializers.VideoAssetSerializer(video_asset)
        return self.response_ok(serializer.data)
