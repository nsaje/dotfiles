import rest_framework.permissions
import rest_framework.serializers

import restapi.common.views_base
import zemauth.access
from core.features.videoassets import constants
from core.features.videoassets import models
from core.features.videoassets import service
from zemauth.features.entity_permission import Permission

from . import serializers


class VideoAssetBaseViewSet(restapi.common.views_base.RESTAPIBaseViewSet):
    permission_classes = [rest_framework.permissions.IsAuthenticated]


class VideoAssetListViewSet(VideoAssetBaseViewSet):
    def post(self, request, account_id):
        account = zemauth.access.get_account(request.user, Permission.WRITE, account_id)
        serializer = serializers.VideoAssetPostSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        if data["upload"]["type"] == constants.VideoAssetType.DIRECT_UPLOAD:
            video_asset, upload_info = service.initiate_asset_for_direct_upload(account, data["name"])
            video_asset.upload = upload_info
            return self.response_ok(serializers.VideoAssetSerializer(video_asset).data)
        elif data["upload"]["type"] == constants.VideoAssetType.VAST_UPLOAD:
            video_asset, upload_info = service.initiate_asset_for_vast_upload(account)
            video_asset.upload = upload_info
            return self.response_ok(serializers.VideoAssetSerializer(video_asset).data)
        elif data["upload"]["type"] == constants.VideoAssetType.VAST_URL:
            try:
                video_asset = service.create_asset_from_vast_url(account, data["vast_url"])
                return self.response_ok(serializers.VideoAssetSerializer(video_asset).data)
            except service.ParseVastError as e:
                raise rest_framework.serializers.ValidationError(str(e))
        else:
            raise rest_framework.serializers.ValidationError("Unsupported upload type")


class VideoAssetViewSet(VideoAssetBaseViewSet):
    def get(self, request, account_id, videoasset_id):
        account = zemauth.access.get_account(request.user, Permission.READ, account_id)
        video_asset = models.VideoAsset.objects.get(account=account, id=videoasset_id)
        serializer = serializers.VideoAssetSerializer(video_asset)
        return self.response_ok(serializer.data)

    def put(self, request, account_id, videoasset_id):
        account = zemauth.access.get_account(request.user, Permission.WRITE, account_id)
        video_asset = models.VideoAsset.objects.get(account=account, id=videoasset_id)

        serializer = serializers.VideoAssetPostSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        if (
            video_asset.type == constants.VideoAssetType.VAST_UPLOAD
            and video_asset.status == constants.VideoAssetStatus.NOT_UPLOADED
            and data["status"] == constants.VideoAssetStatus.PROCESSING
        ):
            try:
                video_asset = service.update_asset_for_vast_upload(account, videoasset_id)
                serializer = serializers.VideoAssetSerializer(video_asset)
                return self.response_ok(serializer.data)

            except service.ParseVastError as e:
                video_asset.status = constants.VideoAssetStatus.PROCESSING_ERROR
                serializer = serializers.VideoAssetSerializer(video_asset)
                data = serializer.data
                data["error_message"] = str(e)
                return self.response_ok(data)
        else:
            raise rest_framework.serializers.ValidationError("Unsupported asset update")
