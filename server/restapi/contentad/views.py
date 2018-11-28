import rest_framework.serializers

import dash.models
from dash.features import contentupload
from dash.views import helpers
from restapi.common.views_base import RESTAPIBaseView
from utils import dates_helper
from utils import exc

from . import serializers

ACCOUNTS_CAN_EDIT_URL = [305]


class ContentAdViewList(RESTAPIBaseView):
    def get(self, request):
        ad_group_id = request.query_params.get("adGroupId")
        if not ad_group_id:
            raise serializers.ValidationError("Must pass adGroupId parameter")
        ad_group = helpers.get_ad_group(request.user, ad_group_id)
        content_ads = (
            dash.models.ContentAd.objects.filter(ad_group=ad_group).exclude_archived().select_related("ad_group")
        )
        serializer = serializers.ContentAdSerializer(content_ads, many=True, context={"request": request})
        return self.response_ok(serializer.data)


class ContentAdViewDetails(RESTAPIBaseView):
    def get(self, request, content_ad_id):
        content_ad = helpers.get_content_ad(request.user, content_ad_id)
        serializer = serializers.ContentAdSerializer(content_ad, context={"request": request})
        return self.response_ok(serializer.data)

    def put(self, request, content_ad_id):
        content_ad = helpers.get_content_ad(request.user, content_ad_id)
        serializer = serializers.ContentAdSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        state = serializer.validated_data.get("state")
        if state is not None and state != content_ad.state:
            content_ad.set_state(request, state)

        url = serializer.validated_data.get("url")
        if url is not None and url != content_ad.url:
            if content_ad.ad_group.campaign.account_id not in ACCOUNTS_CAN_EDIT_URL:
                raise rest_framework.serializers.ValidationError("URL can't be edited via API.")
            content_ad.set_url(request, url)

        content_ad.update(request, **serializer.validated_data)

        return self.response_ok(serializers.ContentAdSerializer(content_ad, context={"request": request}).data)


class ContentAdBatchViewList(RESTAPIBaseView):
    def post(self, request):
        ad_group_id = request.query_params.get("adGroupId")
        if not ad_group_id:
            raise serializers.ValidationError("Must pass adGroupId parameter")
        ad_group = helpers.get_ad_group(request.user, ad_group_id)

        candidates_data = []

        for candidate in request.data:
            serializer = self._get_candidate_serializer(candidate)
            serializer = serializer(data=candidate, context={"request": request})
            serializer.is_valid(raise_exception=True)
            candidates_data.append(serializer.validated_data)

        batch_name = self._generate_batch_name("API Upload")
        filename = None

        batch, candidates = contentupload.upload.insert_candidates(
            request.user, ad_group.campaign.account, candidates_data, ad_group, batch_name, filename, auto_save=True
        )

        batch_serializer = serializers.UploadBatchSerializer(batch, context={"request": request})
        return self.response_ok(batch_serializer.data, status=201)

    @staticmethod
    def _generate_batch_name(prefix):
        return "%s %s" % (prefix, dates_helper.local_now().strftime("%m/%d/%Y %H:%M %z"))

    def _get_candidate_serializer(self, candidate):
        type_serializer = serializers.AdTypeSerializer(data=candidate)
        type_serializer.is_valid(raise_exception=True)
        ad_type = type_serializer.validated_data.get("type")

        if ad_type == dash.constants.AdType.IMAGE:
            return serializers.ImageAdCandidateSerializer
        if ad_type == dash.constants.AdType.AD_TAG:
            return serializers.AdTagCandidateSerializer
        return serializers.ContentAdCandidateSerializer


class ContentAdBatchViewDetails(RESTAPIBaseView):
    def get(self, request, batch_id):
        try:
            batch = dash.models.UploadBatch.objects.get(id=batch_id)
        except dash.models.UploadBatch.DoesNotExist:
            raise exc.MissingDataError("Upload batch does not exist")
        helpers.get_ad_group(request.user, batch.ad_group_id)  # permissions check

        batch_serializer = serializers.UploadBatchSerializer(batch, context={"request": request})
        return self.response_ok(batch_serializer.data)
