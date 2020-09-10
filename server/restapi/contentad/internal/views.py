from rest_framework import permissions

import core.models
import core.models.content_ad.exceptions
import dash.features.clonecontentad
import restapi.common.views_base
import utils.exc
import zemauth.access
from zemauth.features.entity_permission import Permission

from . import serializers


class CloneContentAdsViewSet(restapi.common.views_base.RESTAPIBaseViewSet):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        serializer = serializers.CloneContentAdsSerializer(data=request.data, context=self.get_serializer_context())
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        ad_group = zemauth.access.get_ad_group(request.user, Permission.WRITE, validated_data["ad_group_id"])
        content_ads = core.models.ContentAd.objects.filter(ad_group=ad_group).exclude_archived()

        try:
            destination_edit_batch, candidates = dash.features.clonecontentad.service.clone_edit(
                request,
                ad_group,
                serializers.get_content_ads(content_ads, validated_data),
                zemauth.access.get_ad_group(request.user, Permission.WRITE, validated_data["destination_ad_group_id"]),
                validated_data["destination_batch_name"],
                validated_data.get("state"),
            )

        except core.models.content_ad.exceptions.CampaignAdTypeMismatch as err:
            raise utils.exc.ValidationError(errors={"type": [str(err)]})

        except core.models.content_ad.exceptions.AdGroupIsArchived as err:
            raise utils.exc.ValidationError(errors={"destination_ad_group_id": [str(err)]})

        return self.response_ok(
            {
                "destination_batch": serializers.UploadBatchSerializer(destination_edit_batch).data,
                "candidates": candidates,
            }
        )
