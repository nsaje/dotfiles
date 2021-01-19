import rest_framework.serializers
from django.conf import settings

import core.features.ad_review
import core.models.content_ad.exceptions
import core.models.content_ad_candidate.exceptions
import dash.constants
import dash.models
import zemauth.access
from dash.features import contentupload
from restapi.common.pagination import StandardPagination
from restapi.common.views_base import RESTAPIBaseView
from restapi.common.views_base import RESTAPIBaseViewSet
from restapi.contentad.v1 import serializers
from utils import dates_helper
from utils import exc
from zemauth.features.entity_permission import Permission

ACCOUNTS_CAN_EDIT_URL = [settings.HARDCODED_ACCOUNT_ID_OEN]
ACCOUNTS_CAN_EDIT_BRAND_NAME = [settings.HARDCODED_ACCOUNT_ID_OEN]


class ContentAdViewSet(RESTAPIBaseViewSet):
    def get(self, request, content_ad_id):
        qpe = serializers.ContentAdQueryParams(data=request.query_params)
        qpe.is_valid(raise_exception=True)
        include_approval_status = qpe.validated_data.get("include_approval_status")
        content_ad = zemauth.access.get_content_ad(request.user, Permission.READ, content_ad_id)
        if include_approval_status:
            approval_status_map = core.features.ad_review.get_per_source_submission_status_map([content_ad])
            content_ad.approval_status = approval_status_map.get(content_ad.id, {}).values()
        serializer = serializers.ContentAdSerializer(content_ad, context={"request": request})
        return self.response_ok(serializer.data)

    def list(self, request):
        qpe = serializers.ContentAdListQueryParams(data=request.query_params)
        qpe.is_valid(raise_exception=True)
        ad_group_id = qpe.validated_data.get("ad_group_id")
        ad_group = zemauth.access.get_ad_group(request.user, Permission.READ, ad_group_id)

        content_ads = (
            dash.models.ContentAd.objects.filter(ad_group=ad_group)
            .exclude_archived()
            .select_related("ad_group")
            .order_by("pk")
        )
        paginator = StandardPagination(default_limit=500)
        content_ads_paginated = paginator.paginate_queryset(content_ads, request)

        include_approval_status = qpe.validated_data.get("include_approval_status")
        if include_approval_status:
            approval_status_map = core.features.ad_review.get_per_source_submission_status_map(content_ads_paginated)
            for content_ad in content_ads_paginated:
                content_ad.approval_status = approval_status_map.get(content_ad.id, {}).values()

        return self.response_ok(
            serializers.ContentAdSerializer(content_ads_paginated, many=True, context={"request": request}).data
        )

    def put(self, request, content_ad_id):
        content_ad = zemauth.access.get_content_ad(request.user, Permission.WRITE, content_ad_id)
        serializer = serializers.ContentAdSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        url = serializer.validated_data.get("url")
        if url is not None and url != content_ad.url:
            if content_ad.ad_group.campaign.account_id not in ACCOUNTS_CAN_EDIT_URL:
                raise rest_framework.serializers.ValidationError("URL can't be edited via API.")
        if (
            "brand_name" in serializer.validated_data
            and content_ad.ad_group.campaign.account_id not in ACCOUNTS_CAN_EDIT_BRAND_NAME
        ):
            del serializer.validated_data["brand_name"]

        if "tracker_urls" in serializer.validated_data and "trackers" not in serializer.validated_data:
            serializer.validated_data["trackers"] = dash.features.contentupload.convert_legacy_trackers(
                serializer.validated_data.get("tracker_urls", []), tracker_optional=True
            )

        try:
            content_ad.update(request, **serializer.validated_data)
        except core.models.content_ad.exceptions.CampaignAdTypeMismatch as err:
            raise exc.ValidationError(errors={"type": [str(err)]})

        return self.response_ok(serializers.ContentAdSerializer(content_ad, context={"request": request}).data)


class ContentAdBatchViewList(RESTAPIBaseView):
    def post(self, request):
        qpe = serializers.ContentAdListQueryParams(data=request.query_params)
        qpe.is_valid(raise_exception=True)
        ad_group_id = qpe.validated_data.get("ad_group_id")

        ad_group = zemauth.access.get_ad_group(request.user, Permission.WRITE, ad_group_id)

        candidates_data = []

        for candidate in request.data:
            serializer = self._get_candidate_serializer(candidate)
            serializer = serializer(data=candidate, context={"request": request})
            serializer.is_valid(raise_exception=True)
            candidates_data.append(serializer.validated_data)

        batch_name = self._generate_batch_name("API Upload")
        filename = None

        try:
            batch, candidates = contentupload.upload.insert_candidates(
                request.user, ad_group.campaign.account, candidates_data, ad_group, batch_name, filename, auto_save=True
            )

        except core.models.content_ad_candidate.exceptions.AdGroupIsArchived as err:
            raise exc.ValidationError(str(err))

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
        zemauth.access.get_ad_group(request.user, Permission.READ, batch.ad_group_id)  # permissions check

        batch_serializer = serializers.UploadBatchSerializer(batch, context={"request": request})
        return self.response_ok(batch_serializer.data)
