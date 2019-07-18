from rest_framework import permissions

import core.models
import core.models.content_ad.exceptions
import restapi.access
import restapi.common.views_base
import utils.exc

from . import serializers
from . import service


class CloneContentAds(restapi.common.views_base.RESTAPIBaseView):
    permission_classes = (
        permissions.IsAuthenticated,
        restapi.access.gen_permission_class("zemauth.can_clone_contentads"),
    )

    def post(self, request):
        user = request.user

        form = serializers.CloneContentAdsSerializer(data=request.data, context=self.get_serializer_context())
        form.is_valid(raise_exception=True)

        ad_group = restapi.access.get_ad_group(user, form.validated_data["ad_group_id"])
        content_ads = core.models.ContentAd.objects.filter(ad_group=ad_group).filter_by_user(user).exclude_archived()

        try:
            destination_batch = service.clone(
                request,
                ad_group,
                serializers.get_content_ads(content_ads, form.validated_data),
                restapi.access.get_ad_group(user, form.validated_data["destination_ad_group_id"]),
                form.validated_data["destination_batch_name"],
                form.validated_data.get("state"),
            )

        except core.models.content_ad.exceptions.CampaignAdTypeMismatch as err:
            raise utils.exc.ValidationError(errors={"type": [str(err)]})

        except core.models.content_ad.exceptions.AdGroupIsArchived as err:
            raise utils.exc.ValidationError(errors={"destination_ad_group_id": [str(err)]})

        return self.response_ok(serializers.UploadBatchSerializer(destination_batch).data)
