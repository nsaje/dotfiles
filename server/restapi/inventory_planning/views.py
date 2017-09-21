from rest_framework import permissions
import django.http
import django.utils.cache

from restapi.views import RESTAPIBaseView
import dash.features.inventory_planning

import serializers


CLIENT_SIDE_CACHE_TIME = 60 * 60 * 24  # cache for 1 day

SUMMARY = 'summary'
COUNTRIES = 'countries'
PUBLISHERS = 'publishers'
DEVICE_TYPES = 'device-types'
VALID_BREAKDOWNS = (SUMMARY, COUNTRIES, PUBLISHERS, DEVICE_TYPES)


class InventoryPlanningView(RESTAPIBaseView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, breakdown):
        filters_serializer = serializers.QueryFilterGET(data=request.query_params)
        return self._handle(breakdown, filters_serializer)

    def post(self, request, breakdown):
        filters_serializer = serializers.QueryFilter(data=request.data)
        return self._handle(breakdown, filters_serializer)

    def _handle(self, breakdown, filters_serializer):
        filters_serializer.is_valid(raise_exception=True)
        filters = self._extract_filters(filters_serializer)

        if breakdown == SUMMARY:
            data = dash.features.inventory_planning.get_summary(filters)
            return self._add_cache_headers(data)

        elif breakdown == COUNTRIES:
            data = dash.features.inventory_planning.get_by_country(filters)
            return self._add_cache_headers(data)

        elif breakdown == DEVICE_TYPES:
            data = dash.features.inventory_planning.get_by_device_type(filters)
            return self._add_cache_headers(data)

        elif breakdown == PUBLISHERS:
            data = dash.features.inventory_planning.get_by_publisher(filters)
            return self._add_cache_headers(data)

        else:
            raise django.http.Http404

    @staticmethod
    def _extract_filters(filters_serializer):
        return {field: values for field, values in filters_serializer.validated_data.items() if values}

    def _add_cache_headers(self, data):
        response = self.response_ok(data)
        django.utils.cache.patch_cache_control(response, max_age=CLIENT_SIDE_CACHE_TIME)
        return response
