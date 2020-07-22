import json

import django.http
import django.utils.cache
from rest_framework import permissions
from rest_framework.authentication import SessionAuthentication
from rest_framework.parsers import FormParser
from rest_framework.parsers import JSONParser

import dash.features.inventory_planning
import utils.rest_common.authentication
from restapi.common.views_base import RESTAPIBaseViewSet
from restapi.inventory_planning.internal import serializers
from utils import csv_utils

CLIENT_SIDE_CACHE_TIME = 60 * 60 * 24  # cache for 1 day

SUMMARY = "summary"
COUNTRIES = "countries"
PUBLISHERS = "publishers"
DEVICE_TYPES = "device-types"
MEDIA_SOURCES = "media-sources"
CHANNELS = "channels"

VALID_BREAKDOWNS = (SUMMARY, COUNTRIES, PUBLISHERS, DEVICE_TYPES, MEDIA_SOURCES, CHANNELS)


class CsrfExemptSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, request):
        return


class InventoryPlanningView(RESTAPIBaseViewSet):
    authentication_classes = [utils.rest_common.authentication.OAuth2Authentication, CsrfExemptSessionAuthentication]
    permission_classes = (permissions.IsAuthenticated,)
    parser_classes = (JSONParser, FormParser)

    def export(self, request):
        data = request.data.get("data")
        data = json.loads(data) if data else request.data

        filters_serializer = serializers.QueryFilter(data=data)
        filters_serializer.is_valid(raise_exception=True)
        filters = self._extract_filters(filters_serializer)

        csv_data = self._format_inventory_csv_data(request, filters)
        csv = csv_utils.tuplelist_to_csv(csv_data)

        return csv_utils.create_csv_response(data=csv, filename="inventory_data_export")

    def get(self, request, breakdown):
        filters_serializer = serializers.QueryFilterGET(data=request.query_params)
        filters_serializer.is_valid(raise_exception=True)
        filters = self._extract_filters(filters_serializer)
        breakdown_data = self._handle_breakdown(request, breakdown, filters)
        return self._response_with_cache_headers(breakdown_data)

    def post(self, request, breakdown):
        filters_serializer = serializers.QueryFilter(data=request.data)
        filters_serializer.is_valid(raise_exception=True)
        filters = self._extract_filters(filters_serializer)
        breakdown_data = self._handle_breakdown(request, breakdown, filters)
        return self._response_with_cache_headers(breakdown_data)

    def _handle_breakdown(self, request, breakdown, filters):
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

        elif breakdown == CHANNELS:
            data = dash.features.inventory_planning.get_by_channel(request, filters)
            data = self._remap_breakdown(data, value_field="channel")

        else:
            raise django.http.Http404

        return data

    @staticmethod
    def _extract_filters(filters_serializer):
        return {field: values for field, values in list(filters_serializer.validated_data.items()) if values}

    @staticmethod
    def _remap_summary(request, data):
        if not data:
            return {}

        avg_cpc = (data["total_win_price"] / 1000 / float(data["redirects"])) if data["redirects"] else None
        avg_cpm = (data["total_win_price"] / float(data["win_notices"])) if data["win_notices"] else None
        win_ratio = (data["win_notices"] / float(data["bids"])) if data["bids"] else None

        return {"auction_count": data.get("slots"), "avg_cpc": avg_cpc, "avg_cpm": avg_cpm, "win_ratio": win_ratio}

    @staticmethod
    def _remap_breakdown(data, value_field):
        return [
            {"name": item.get("name"), "value": item[value_field], "auction_count": item.get("slots")} for item in data
        ]

    def _response_with_cache_headers(self, data):
        response = self.response_ok(data)
        django.utils.cache.patch_cache_control(response, max_age=CLIENT_SIDE_CACHE_TIME)
        return response

    def _format_inventory_csv_data(self, request, filters):
        countries_data = self._handle_breakdown(request, COUNTRIES, filters)
        publishers_data = self._handle_breakdown(request, PUBLISHERS, filters)
        device_types_data = self._handle_breakdown(request, DEVICE_TYPES, filters)
        media_sources_data = self._handle_breakdown(request, MEDIA_SOURCES, filters)
        channels_data = self._handle_breakdown(request, CHANNELS, filters)

        csv_data = []

        if filters:
            country_filter = filters.get("country")
            publisher_filter = filters.get("publisher")
            device_filter = filters.get("device_type")
            source_filter = filters.get("source_id")
            channels_filter = filters.get("channel")

            csv_data.append(("Active filters",))

            if country_filter:
                countries_map = dash.features.inventory_planning.get_countries_map()
                csv_data = csv_utils.insert_csv_row(
                    csv_data, "Countries", [countries_map.get(c, c) for c in country_filter]
                )

            if publisher_filter:
                csv_data = csv_utils.insert_csv_row(csv_data, "Publishers", publisher_filter)

            if device_filter:
                device_types_map = dict(dash.features.inventory_planning.constants.InventoryDeviceType.get_choices())
                csv_data = csv_utils.insert_csv_row(
                    csv_data, "Devices", [device_types_map.get(dt, dt) for dt in device_filter]
                )

            if source_filter:
                sources_map = dash.features.inventory_planning.get_filtered_sources_map(request, filters)
                csv_data = csv_utils.insert_csv_row(csv_data, "SSPs", [sources_map.get(s, s) for s in source_filter])

            if channels_filter:
                csv_data = csv_utils.insert_csv_row(csv_data, "Channels", channels_filter)

        csv_data = csv_utils.insert_csv_paragraph(csv_data, "Devices", device_types_data, "name", "auction_count")
        csv_data = csv_utils.insert_csv_paragraph(csv_data, "SSPs", media_sources_data, "name", "auction_count")
        csv_data = csv_utils.insert_csv_paragraph(csv_data, "Countries", countries_data, "name", "auction_count")
        csv_data = csv_utils.insert_csv_paragraph(csv_data, "Channels", channels_data, "name", "auction_count")
        csv_data = csv_utils.insert_csv_paragraph(
            csv_data, "Publishers", publishers_data[:1000], "value", "auction_count"
        )

        return csv_data
