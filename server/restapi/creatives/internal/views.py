import rest_framework.permissions
import rest_framework.response
from django.db import transaction
from django.db.models import Q
from djangorestframework_camel_case.parser import CamelCaseJSONParser

import core.features.creatives
import dash.constants
import restapi.common.parsers
import utils.exc
import zemauth.access
from restapi.common.pagination import StandardPagination
from restapi.common.views_base import RESTAPIBaseViewSet
from zemauth.features.entity_permission import Permission

from . import helpers
from . import serializers


class CanUseCreativeView(rest_framework.permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.has_perm("zemauth.can_see_creative_library"))


class CreativeBaseViewSet(RESTAPIBaseViewSet):
    permission_classes = (rest_framework.permissions.IsAuthenticated, CanUseCreativeView)


class CreativeViewSet(CreativeBaseViewSet):
    serializer = serializers.CreativeSerializer

    def get(self, request, creative_id):
        creative = zemauth.access.get_creative(request.user, Permission.READ, creative_id)
        return self.response_ok(self.serializer(creative, context={"request": request}).data)

    def list(self, request):
        qpe = serializers.CreativeQueryParams(data=request.query_params)
        qpe.is_valid(raise_exception=True)

        agency_id = qpe.validated_data.get("agency_id")
        account_id = qpe.validated_data.get("account_id")

        if account_id is not None:
            account = zemauth.access.get_account(request.user, Permission.READ, account_id)
            creatives_qs = (
                core.features.creatives.Creative.objects.filter_by_account(account)
                .select_related("agency", "account")
                .order_by("-created_dt")
            )
        elif agency_id is not None:
            agency = zemauth.access.get_agency(request.user, Permission.READ, agency_id)
            creatives_qs = (
                core.features.creatives.Creative.objects.filter_by_agency_and_related_accounts(agency)
                .select_related("agency", "account")
                .order_by("-created_dt")
            )
        else:
            raise utils.exc.ValidationError(
                errors={"non_field_errors": "Either agency id or account id must be provided."}
            )

        keyword = qpe.validated_data.get("keyword")
        if keyword is not None:
            creatives_qs = self._filter_by_keyword(creatives_qs, keyword)

        creative_type = qpe.validated_data.get("creative_type")
        if creative_type is not None:
            creatives_qs = self._filter_by_creative_type(creatives_qs, creative_type)

        tags = qpe.validated_data.get("tags")
        if tags is not None:
            creatives_qs = self._filter_by_tags(creatives_qs, tags)

        paginator = StandardPagination()
        creatives_qs_paginated = paginator.paginate_queryset(creatives_qs, request)
        return paginator.get_paginated_response(
            self.serializer(creatives_qs_paginated, many=True, context={"request": request}).data
        )

    @staticmethod
    def _filter_by_keyword(queryset, value):
        return queryset.filter(Q(url__icontains=value) | Q(title__icontains=value) | Q(description__icontains=value))

    @staticmethod
    def _filter_by_creative_type(queryset, value):
        return queryset.filter(type=value)

    @staticmethod
    def _filter_by_tags(queryset, value):
        return queryset.filter(tags__name__in=value)


class CreativeBatchViewSet(CreativeBaseViewSet):
    serializer = serializers.CreativeBatchSerializer

    def get(self, request, batch_id):
        batch = zemauth.access.get_creative_batch(request.user, Permission.READ, batch_id)
        return self.response_ok(self.serializer(batch, context={"request": request}).data)

    def validate(self, request):
        serializer = self.serializer(data=request.data, partial=True, context={"request": request})
        serializer.is_valid(raise_exception=True)
        return self.response_ok(None)

    def create(self, request):
        serializer = self.serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        agency_id = data.get("agency_id")
        data["agency"] = (
            zemauth.access.get_agency(request.user, Permission.WRITE, agency_id) if agency_id is not None else None
        )

        account_id = data.get("account_id")
        data["account"] = (
            zemauth.access.get_account(request.user, Permission.WRITE, account_id) if account_id is not None else None
        )

        with transaction.atomic():
            batch = core.features.creatives.CreativeBatch.objects.create(
                request,
                data.get("name", helpers.generate_batch_name()),
                agency=data.get("agency"),
                account=data.get("account"),
                mode=data.get("mode"),
                type=data.get("type"),
            )
            batch.update(request, **data)
            batch.set_creative_tags(request, data.get("tags"))

        return self.response_ok(self.serializer(batch, context={"request": request}).data, status=201)

    def put(self, request, batch_id):
        serializer = self.serializer(data=request.data, partial=True, context={"request": request})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        batch = zemauth.access.get_creative_batch(request.user, Permission.WRITE, batch_id)
        batch.update(request, **data)

        tags = data.get("tags")
        if tags is not None:
            batch.set_creative_tags(request, tags)

        return self.response_ok(self.serializer(batch, context={"request": request}).data)

    def upload(self, request, batch_id):
        batch = zemauth.access.get_creative_batch(request.user, Permission.WRITE, batch_id)

        candidates = []
        for candidate in batch.creativecandidate_set.all():
            candidate_dict = candidate.to_dict()

            ad_type_serializer = serializers.AdTypeSerializer(data=candidate_dict)
            ad_type_serializer.is_valid(raise_exception=True)
            ad_type = ad_type_serializer.validated_data.get("type")

            serializer_class = self._get_serializer_class(ad_type)
            serializer = serializer_class(data=candidate_dict, context={"request": request})
            serializer.is_valid(raise_exception=True)

            candidates.append(serializer.validated_data)

        with transaction.atomic():
            core.features.creatives.Creative.objects.bulk_create_from_candidates(request, batch, candidates)
            batch.mark_done(request)

        return rest_framework.response.Response(None, status=201)

    @staticmethod
    def _get_serializer_class(ad_type):
        if ad_type == dash.constants.AdType.VIDEO:
            return serializers.VideoCreativeSerializer
        if ad_type == dash.constants.AdType.IMAGE:
            return serializers.ImageCreativeSerializer
        if ad_type == dash.constants.AdType.AD_TAG:
            return serializers.AdTagCreativeSerializer
        return serializers.NativeCreativeSerializer


class CreativeCandidateViewSet(CreativeBaseViewSet):
    serializer = serializers.CreativeCandidateSerializer
    parser_classes = (
        restapi.common.parsers.CamelCaseJSONMultiPartParser,
        CamelCaseJSONParser,
    )

    def list(self, request, batch_id):
        batch = zemauth.access.get_creative_batch(request.user, Permission.READ, batch_id)

        candidates_qs = core.features.creatives.CreativeCandidate.objects.filter_by_batch(batch)

        paginator = StandardPagination()
        candidates_qs_paginated = paginator.paginate_queryset(candidates_qs, request)
        return paginator.get_paginated_response(
            self.serializer(candidates_qs_paginated, many=True, context={"request": request}).data
        )

    def get(self, request, batch_id, candidate_id):
        batch = zemauth.access.get_creative_batch(request.user, Permission.READ, batch_id)
        candidate = self._get_candidate(batch, candidate_id)

        return self.response_ok(self.serializer(candidate, context={"request": request}).data)

    # TODO (msuber): add support for mode (edit, clone) and bulk create
    def create(self, request, batch_id):
        batch = zemauth.access.get_creative_batch(request.user, Permission.WRITE, batch_id)

        with transaction.atomic():
            candidate = core.features.creatives.CreativeCandidate.objects.create(batch)

        return self.response_ok(self.serializer(candidate, context={"request": request}).data, status=201)

    def put(self, request, batch_id, candidate_id):
        batch = zemauth.access.get_creative_batch(request.user, Permission.WRITE, batch_id)

        ad_type_serializer = serializers.AdTypeSerializer(data=request.data)
        ad_type_serializer.is_valid(raise_exception=True)
        ad_type = ad_type_serializer.validated_data.get("type")

        serializer_class = self._get_serializer_class(ad_type)

        serializer = serializer_class(data=request.data, partial=True, context={"request": request})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        candidate = self._get_candidate(batch, candidate_id)
        candidate.update(request, **data)

        tags = data.get("tags")
        if tags is not None:
            candidate.set_creative_tags(request, tags)

        return self.response_ok(self.serializer(candidate, context={"request": request}).data)

    def remove(self, request, batch_id, candidate_id):
        batch = zemauth.access.get_creative_batch(request.user, Permission.WRITE, batch_id)
        candidate = self._get_candidate(batch, candidate_id)
        candidate.delete()
        return rest_framework.response.Response(None, status=204)

    @staticmethod
    def _get_candidate(batch, candidate_id):
        try:
            candidate = core.features.creatives.CreativeCandidate.objects.filter_by_batch(batch).get(pk=candidate_id)
        except core.features.creatives.CreativeCandidate.DoesNotExist:
            raise utils.exc.MissingDataError("Candidate does not exist!")
        return candidate

    @staticmethod
    def _get_serializer_class(ad_type):
        if ad_type == dash.constants.AdType.VIDEO:
            return serializers.VideoCreativeCandidateSerializer
        if ad_type == dash.constants.AdType.IMAGE:
            return serializers.ImageCreativeCandidateSerializer
        if ad_type == dash.constants.AdType.AD_TAG:
            return serializers.AdTagCreativeCandidateSerializer
        return serializers.NativeCreativeCandidateSerializer
