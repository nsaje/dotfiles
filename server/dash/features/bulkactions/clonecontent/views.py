from rest_framework import permissions
from djangorestframework_camel_case.render import CamelCaseJSONRenderer
from djangorestframework_camel_case.parser import CamelCaseJSONParser

import core.entity
import restapi.access
import restapi.views

import serializers
import service


class CloneContentAds(restapi.views.RESTAPIBaseView):
    permission_classes = (permissions.IsAuthenticated,
                          restapi.access.gen_permission_class('zemauth.can_clone_contentads'))

    renderer_classes = (CamelCaseJSONRenderer,)
    parser_classes = (CamelCaseJSONParser,)

    input_serializer = serializers.CloneContentAdsSerializer
    output_serializer = serializers.UploadBatchSerializer

    def post(self, request):
        user = request.user

        form = self.input_serializer(data=request.data, context=self.get_serializer_context())
        form.is_valid(raise_exception=True)

        ad_group = restapi.access.get_ad_group(user, form.validated_data['ad_group_id'])
        content_ads = core.entity.ContentAd.objects.filter(ad_group=ad_group).filter_by_user(user).exclude_archived()

        destination_batch = service.clone(
            request,
            ad_group,
            serializers.get_content_ads(content_ads, form.validated_data),
            restapi.access.get_ad_group(user, form.validated_data['destination_ad_group_id']),
            form.validated_data.get('state'))

        return self.response_ok(self.output_serializer(destination_batch).data)


class InternalCloneContentAds(CloneContentAds):

    input_serializer = serializers.CloneContentAdsInternalSerializer
    output_serializer = serializers.UploadBatchInternalSerializer
