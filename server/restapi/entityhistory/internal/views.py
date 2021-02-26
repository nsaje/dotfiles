from rest_framework import permissions

import core.features.history.models
import zemauth.access
from restapi.common.views_base import RESTAPIBaseViewSet
from restapi.entityhistory.internal import serializers
from zemauth.features.entity_permission import Permission

DEFAULT_ORDER = "-created_dt"


class EntityHistoryViewSet(RESTAPIBaseViewSet):
    permission_classes = (permissions.IsAuthenticated,)

    def list(self, request):
        qpe = serializers.EntityHistoryQueryParams(data=request.query_params)
        qpe.is_valid(raise_exception=True)

        entity_history_filter = self._get_filter(qpe, request.user)
        order = qpe.validated_data.get("order", DEFAULT_ORDER)

        entity_history = (
            core.features.history.models.History.objects.filter(**entity_history_filter)
            .order_by(order)
            .select_related("created_by")
        )

        return self.response_ok(
            serializers.EntityHistorySerializer(entity_history, many=True, context={"request": request}).data
        )

    def _get_filter(self, qpe, user):
        entity_history_filter = {}

        ad_group_id = qpe.validated_data.get("ad_group_id")
        if ad_group_id:
            entity_history_filter["ad_group"] = zemauth.access.get_ad_group(user, Permission.READ, ad_group_id)

        campaign_id = qpe.validated_data.get("campaign_id")
        if campaign_id:
            entity_history_filter["campaign"] = zemauth.access.get_campaign(user, Permission.READ, campaign_id)

        account_id = qpe.validated_data.get("account_id")
        if account_id:
            entity_history_filter["account"] = zemauth.access.get_account(user, Permission.READ, account_id)

        agency_id = qpe.validated_data.get("agency_id")
        if agency_id:
            entity_history_filter["agency"] = zemauth.access.get_agency(user, Permission.READ, agency_id)

        level = qpe.validated_data.get("level")
        if level:
            entity_history_filter["level"] = level

        from_date = qpe.validated_data.get("from_date")
        if from_date:
            entity_history_filter["created_dt__date__gte"] = from_date

        return entity_history_filter
