import newrelic.agent
import rest_framework.permissions
from django.core.cache import caches
from rest_framework.response import Response
from rest_framework.utils.urls import replace_query_param

import restapi.common.pagination
import restapi.common.views_base
import stats.api_realtimestats
import utils.camel_case
import zemauth.access
from utils import camel_case
from utils import exc
from utils.cache_helper import get_cache_key
from zemauth.features.entity_permission import Permission

from . import serializers

GROUPBY_COUNT_CACHE_TIMEOUT = 30
GROUPBY_COUNT_CACHE_PREFIX = "realtimestats_count"

groupby_count_cache = caches["cluster_level_cache"]


class CanUseRealTimeStats(rest_framework.permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.has_perm("zemauth.can_use_realtimestats_api"))


class RealtimeStatsViewSet(restapi.common.views_base.RESTAPIBaseViewSet):
    permission_classes = (rest_framework.permissions.IsAuthenticated, CanUseRealTimeStats)

    @newrelic.agent.function_trace()
    def groupby(self, request):
        serializer = serializers.GroupByQueryParamsExpectations
        query_params = self._extract_query_params(request, serializer=serializer)
        rows = stats.api_realtimestats.groupby(**query_params)
        count_params = {param: value for param, value in query_params.items() if param not in ["limit", "marker"]}
        count = self._get_groupby_count(**count_params)
        return Response(
            {
                "count": count,
                "next": self._get_next_link(request, rows, query_params),
                "data": serializers.RealtimeStatsSerializer(rows, many=True).data,
            }
        )

    def _get_groupby_count(self, **kwargs):
        cache_key = get_cache_key(GROUPBY_COUNT_CACHE_PREFIX, **kwargs)

        cached_value = groupby_count_cache.get(cache_key)
        if cached_value:
            return cached_value

        value = stats.api_realtimestats.count_rows(**kwargs)
        groupby_count_cache.set(cache_key, value, timeout=GROUPBY_COUNT_CACHE_TIMEOUT)

        return value

    @newrelic.agent.function_trace()
    def topn(self, request):
        serializer = serializers.TopNQueryParamsExpectations
        query_params = self._extract_query_params(request, serializer=serializer)
        rows = stats.api_realtimestats.topn(**query_params)
        return self.response_ok(serializers.RealtimeStatsSerializer(rows, many=True).data)

    def _extract_query_params(self, request, *, serializer):
        qpe = serializer(data=request.query_params)
        qpe.is_valid(raise_exception=True)

        query_params = {}
        query_params.update(self._extract_dimensions_filter(request, qpe))

        query_params["breakdown"] = []
        if qpe.validated_data.get("breakdown"):
            breakdown = utils.camel_case.camel_to_snake(qpe.validated_data.get("breakdown"))
            query_params["breakdown"].append(breakdown)

        marker = qpe.validated_data.get("marker")
        if marker:
            query_params["marker"] = marker

        limit = qpe.validated_data.get("limit")
        if limit:
            query_params["limit"] = limit

        order = qpe.validated_data.get("order")
        if order:
            query_params["order"] = order

        return query_params

    def _extract_dimensions_filter(self, request, qpe):
        dimensions_filter = {}

        account_id = qpe.validated_data.get("account_id")
        if account_id:
            dimensions_filter["account_id"] = account_id
            zemauth.access.get_account(request.user, Permission.READ, dimensions_filter["account_id"])

        campaign_id = qpe.validated_data.get("campaign_id")
        if campaign_id:
            dimensions_filter["campaign_id"] = campaign_id
            zemauth.access.get_campaign(request.user, Permission.READ, dimensions_filter["campaign_id"])

        ad_group_id = qpe.validated_data.get("ad_group_id")
        if ad_group_id:
            dimensions_filter["ad_group_id"] = ad_group_id
            zemauth.access.get_ad_group(request.user, Permission.READ, dimensions_filter["ad_group_id"])

        content_ad_id = qpe.validated_data.get("content_ad_id")
        if content_ad_id:
            dimensions_filter["content_ad_id"] = content_ad_id
            zemauth.access.get_content_ad(request.user, Permission.READ, dimensions_filter["content_ad_id"])

        expected_fields = ["account_id", "campaign_id", "ad_group_id", "content_ad_id"]
        if not any(val for key, val in dimensions_filter.items() if key in expected_fields):
            raise exc.ValidationError(
                "No dimension filter provided. Expected at least one of: %s"
                % (", ".join(map(camel_case.snake_to_camel, expected_fields)))
            )

        return dimensions_filter

    def _get_next_link(self, request, rows, query_params):
        limit = query_params["limit"]
        if limit > len(rows):
            return None

        url = request.build_absolute_uri()
        url = replace_query_param(url, "limit", limit)

        breakdown = query_params["breakdown"][0]
        new_marker = rows[-1][breakdown]
        return replace_query_param(url, "marker", new_marker)
