from rest_framework import permissions

import core.entity
import restapi.access
import restapi.views

import serializers
import service


class CloneContentAds(restapi.views.RESTAPIBaseView):
    permission_classes = (permissions.IsAuthenticated,
                          restapi.access.gen_permission_class('zemauth.can_clone_contentads'))

    def post(self, request):
        user = request.user

        form = serializers.CloneContentAdsSerializer(data=request.data, context=self.get_serializer_context())
        form.is_valid(raise_exception=True)

        ad_group = restapi.access.get_ad_group(user, form.validated_data['ad_group_id'])
        content_ads = core.entity.ContentAd.objects.filter(ad_group=ad_group).filter_by_user(user).exclude_archived()

        destination_batch = service.clone(
            request,
            ad_group,
            serializers.get_content_ads(content_ads, form.validated_data),
            restapi.access.get_ad_group(user, form.validated_data['destination_ad_group_id']),
            form.validated_data['destination_batch_name'], form.validated_data.get('state'))

        return self.response_ok(serializers.UploadBatchSerializer(destination_batch).data)
