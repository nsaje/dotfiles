import rest_framework.permissions
import rest_framework.serializers
from django.db import transaction

import core.models
import restapi.access
import restapi.adgroup.v1.views
from dash import constants
from prodops import hacks

from . import helpers
from . import serializers


class AdGroupViewSet(restapi.adgroup.v1.views.AdGroupViewSet):
    permission_classes = (rest_framework.permissions.IsAuthenticated,)

    def validate(self, request):
        serializer = serializers.AdGroupSerializer(data=request.data, partial=True, context={"request": request})
        serializer.is_valid(raise_exception=True)
        return self.response_ok(None)

    def defaults(self, request):
        campaign_id = request.query_params.get("campaignId", None)
        if not campaign_id:
            raise rest_framework.serializers.ValidationError("Must pass campaignId parameter")
        campaign = restapi.access.get_campaign(request.user, campaign_id)
        ad_group = core.models.AdGroup.objects.get_default(request, campaign)
        extra_data = helpers.get_extra_data(request.user, ad_group)
        return self.response_ok(
            data=serializers.AdGroupSerializer(ad_group.settings, context={"request": request}).data,
            extra=serializers.ExtraDataSerializer(extra_data, context={"request": request}).data,
        )

    def get(self, request, ad_group_id):
        ad_group = restapi.access.get_ad_group(request.user, ad_group_id)
        extra_data = helpers.get_extra_data(request.user, ad_group)
        return self.response_ok(
            data=serializers.AdGroupSerializer(ad_group.settings, context={"request": request}).data,
            extra=serializers.ExtraDataSerializer(extra_data, context={"request": request}).data,
        )

    def put(self, request, ad_group_id):
        ad_group = restapi.access.get_ad_group(request.user, ad_group_id)
        if ad_group.settings.b1_sources_group_enabled != request.data.get(
            "manage_rtb_sources_as_one", ad_group.settings.b1_sources_group_enabled
        ):
            request.data.update(
                {"state": constants.AdGroupSettingsState.get_name(constants.AdGroupSettingsState.INACTIVE)}
            )
        serializer = serializers.AdGroupSerializer(data=request.data, partial=True, context={"request": request})
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            self._update_settings(request, ad_group, serializer.validated_data)

        return self.response_ok(serializers.AdGroupSerializer(ad_group.settings, context={"request": request}).data)

    def create(self, request):
        serializer = serializers.AdGroupSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        settings = serializer.validated_data
        campaign = restapi.access.get_campaign(request.user, settings.get("ad_group", {}).get("campaign_id"))

        with transaction.atomic():
            new_ad_group = core.models.AdGroup.objects.create(
                request, campaign=campaign, name=settings.get("ad_group_name", None)
            )
            self._update_settings(request, new_ad_group, settings)
            hacks.apply_ad_group_create_hacks(request, new_ad_group)

        return self.response_ok(
            serializers.AdGroupSerializer(new_ad_group.settings, context={"request": request}).data, status=201
        )
