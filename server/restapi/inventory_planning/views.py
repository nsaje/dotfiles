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
            data = self._remap_summary(data)

        elif breakdown == COUNTRIES:
            data = dash.features.inventory_planning.get_by_country(filters)
            data = self._remap_breakdown(data, value_field='country')

        elif breakdown == DEVICE_TYPES:
            data = dash.features.inventory_planning.get_by_device_type(filters)
            data = self._remap_breakdown(data, value_field='device_type')

        elif breakdown == PUBLISHERS:
            data = dash.features.inventory_planning.get_by_publisher(filters)
            data = self._remap_breakdown(data, value_field='publisher')

        else:
            raise django.http.Http404

        return self._response_with_cache_headers(data)

    @staticmethod
    def _extract_filters(filters_serializer):
        return {field: values for field, values in filters_serializer.validated_data.items() if values}

    @staticmethod
    def _remap_summary(data):
        if not data:
            return {}
        print data
        return {
            'auction_count': data['bid_reqs'],
            'avg_cpm': data['total_win_price'] / float(data['win_notices'] or float('nan')) * 1000,
            'win_ratio': data['win_notices'] / float(data['bids'] or float('nan'))
        }

    @staticmethod
    def _remap_breakdown(data, value_field):
        return [{
            'name': item.get('name'),
            'value': item[value_field],
            'auction_count': item['bid_reqs'],
        } for item in data]

    def _response_with_cache_headers(self, data):
        response = self.response_ok(data)
        django.utils.cache.patch_cache_control(response, max_age=CLIENT_SIDE_CACHE_TIME)
        return response
