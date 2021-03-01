import newrelic.agent
import rest_framework.permissions

import stats.api_realtimestats
import utils.camel_case
import zemauth.access
from restapi.common.views_base import RESTAPIBaseViewSet
from utils import camel_case
from utils import exc
from zemauth.features.entity_permission import Permission

from . import serializers


class CanUseRealTimeStats(rest_framework.permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.has_perm("zemauth.can_use_realtimestats_api"))


class RealtimeStatsViewSet(RESTAPIBaseViewSet):
    permission_classes = (rest_framework.permissions.IsAuthenticated, CanUseRealTimeStats)

    @newrelic.agent.function_trace()
    def groupby(self, request):
        serializer = serializers.GroupByQueryParamsExpectations
        query_params = self._extract_query_params(request, serializer=serializer)
        rows = stats.api_realtimestats.groupby(**query_params)
        return self.response_ok(serializers.RealtimeStatsSerializer(rows, many=True).data)

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
