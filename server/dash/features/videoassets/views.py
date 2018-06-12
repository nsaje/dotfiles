import rest_framework.serializers
import rest_framework.permissions

import restapi.common.views_base
from . import constants
from . import serializers
from . import models
from . import service


class VideoAssetBaseView(restapi.common.views_base.RESTAPIBaseView):

    permission_classes = (rest_framework.permissions.IsAuthenticated,
                          restapi.access.HasAccountAccess,
                          restapi.access.gen_permission_class('zemauth.fea_video_upload'))


class VideoAssetListView(VideoAssetBaseView):

    def post(self, request, account_id):
        account = restapi.access.get_account(request.user, account_id)
        serializer = serializers.VideoAssetPostSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        if data['upload']['type'] == constants.VideoAssetType.DIRECT_UPLOAD:
            video_asset, upload_info = service.initiate_asset_for_direct_upload(account, data['name'])
            video_asset.upload = upload_info
            return self.response_ok(serializers.VideoAssetSerializer(video_asset).data)
        elif data['upload']['type'] == constants.VideoAssetType.VAST_UPLOAD:
            video_asset, upload_info = service.initiate_asset_for_vast_upload(account)
            video_asset.upload = upload_info
            return self.response_ok(serializers.VideoAssetSerializer(video_asset).data)
        elif data['upload']['type'] == constants.VideoAssetType.VAST_URL:
            #  raise rest_framework.serializers.ValidationError("Not a valid vast file url")
            video_asset = service.create_asset_from_vast_url(account, data['vast_url'])
            return self.response_ok(serializers.VideoAssetSerializer(video_asset).data)
        else:
            return self.response_error("Unsupported upload type")


class VideoAssetView(VideoAssetBaseView):

    def get(self, request, account_id, videoasset_id):
        account = restapi.access.get_account(request.user, account_id)
        video_asset = models.VideoAsset.objects.get(account=account, id=videoasset_id)
        serializer = serializers.VideoAssetSerializer(video_asset)
        return self.response_ok(serializer.data)

    def put(self, request, account_id, videoasset_id):
        account = restapi.access.get_account(request.user, account_id)
        video_asset = models.VideoAsset.objects.get(account=account, id=videoasset_id)

        serializer = serializers.VideoAssetPostSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        if (video_asset.type == constants.VideoAssetType.VAST_UPLOAD and
                video_asset.status == constants.VideoAssetStatus.NOT_UPLOADED and
                data['status'] == constants.VideoAssetStatus.PROCESSING):

            video_asset.status = constants.VideoAssetStatus.READY_FOR_USE
            video_asset.save()

            serializer = serializers.VideoAssetSerializer(video_asset)
            return self.response_ok(serializer.data)
        else:
            return self.response_error("Unsupported asset update")
