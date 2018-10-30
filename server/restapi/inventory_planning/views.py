import django.http
import django.utils.cache
from rest_framework import permissions

import dash.features.inventory_planning
from restapi.common.views_base import RESTAPIBaseView

from . import serializers

CLIENT_SIDE_CACHE_TIME = 60 * 60 * 24  # cache for 1 day

SUMMARY = "summary"
COUNTRIES = "countries"
PUBLISHERS = "publishers"
DEVICE_TYPES = "device-types"
MEDIA_SOURCES = "media-sources"
VALID_BREAKDOWNS = (SUMMARY, COUNTRIES, PUBLISHERS, DEVICE_TYPES, MEDIA_SOURCES)


class InventoryPlanningView(RESTAPIBaseView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, breakdown):
        filters_serializer = serializers.QueryFilterGET(data=request.query_params)
        return self._handle(request, breakdown, filters_serializer)

    def post(self, request, breakdown):
        filters_serializer = serializers.QueryFilter(data=request.data)
        return self._handle(request, breakdown, filters_serializer)

    def _handle(self, request, breakdown, filters_serializer):
        filters_serializer.is_valid(raise_exception=True)
        filters = self._extract_filters(filters_serializer)

        if breakdown == SUMMARY:
            data = dash.features.inventory_planning.get_summary(request, filters)
            data = self._remap_summary(request, data)

        elif breakdown == COUNTRIES:
            data = dash.features.inventory_planning.get_by_country(request, filters)
            data = self._remap_breakdown(data, value_field="country")

        elif breakdown == DEVICE_TYPES:
            data = dash.features.inventory_planning.get_by_device_type(request, filters)
            data = self._remap_breakdown(data, value_field="device_type")

        elif breakdown == PUBLISHERS:
            data = dash.features.inventory_planning.get_by_publisher(request, filters)
            data = self._remap_breakdown(data, value_field="publisher")

        elif breakdown == MEDIA_SOURCES:
            data = dash.features.inventory_planning.get_by_media_source(request, filters)
            data = self._remap_breakdown(data, value_field="source_id")

        else:
            raise django.http.Http404

        return self._response_with_cache_headers(data)

    @staticmethod
    def _extract_filters(filters_serializer):
        return {field: values for field, values in list(filters_serializer.validated_data.items()) if values}

    @staticmethod
    def _remap_summary(request, data):
        if not data:
            return {}

        avg_ctr = InventoryPlanningView._get_source_ctr(request)

        return {
            "auction_count": data["bid_reqs"],
            "avg_cpm": (data["total_win_price"] / float(data["win_notices"])) if data["win_notices"] else None,
            "avg_cpc": (data["total_win_price"] / float(data["win_notices"]) / 1000 / avg_ctr)
            if data["win_notices"]
            else None,
            "win_ratio": (data["win_notices"] / float(data["bids"])) if data["bids"] else None,
        }

    @staticmethod
    def _get_source_ctr(request):
        if dash.features.inventory_planning.has_mediamond_credentials(request):
            return dash.features.inventory_planning.constants.SourceCtr.MEDIAMOND

        if dash.features.inventory_planning.has_rcs_credentials(request):
            return dash.features.inventory_planning.constants.SourceCtr.RCS

        if dash.features.inventory_planning.has_newscorp_credentials(request):
            return dash.features.inventory_planning.constants.SourceCtr.NEWSCORP

        return dash.features.inventory_planning.constants.SourceCtr.AVG

    @staticmethod
    def _remap_breakdown(data, value_field):
        return [
            {"name": item.get("name"), "value": item[value_field], "auction_count": item["bid_reqs"]} for item in data
        ]

    def _response_with_cache_headers(self, data):
        response = self.response_ok(data)
        django.utils.cache.patch_cache_control(response, max_age=CLIENT_SIDE_CACHE_TIME)
        return response
