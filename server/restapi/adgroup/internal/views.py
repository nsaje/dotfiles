import rest_framework.permissions
import rest_framework.serializers
from django.db import transaction

import core.models
import prodops.hacks
import restapi.access
import restapi.adgroup.v1.views
import utils.exc
from dash import constants

from . import helpers
from . import serializers


class AdGroupViewSet(restapi.adgroup.v1.views.AdGroupViewSet):
    permission_classes = (rest_framework.permissions.IsAuthenticated,)
    serializer = serializers.AdGroupSerializer

    def validate(self, request):
        serializer = self.serializer(data=request.data, partial=True, context={"request": request})
        serializer.is_valid(raise_exception=True)
        return self.response_ok(None)

    def defaults(self, request):
        campaign_id = request.query_params.get("campaignId", None)
        if not campaign_id:
            raise rest_framework.serializers.ValidationError("Must pass campaignId parameter")
        campaign = restapi.access.get_campaign(request.user, campaign_id)
        ad_group = core.models.AdGroup.objects.get_default(request, campaign)
        self._augment_ad_group(request, ad_group)
        extra_data = helpers.get_extra_data(request.user, ad_group)
        return self.response_ok(
            data=self.serializer(ad_group.settings, context={"request": request}).data,
            extra=serializers.ExtraDataSerializer(extra_data, context={"request": request}).data,
        )

    def get(self, request, ad_group_id):
        ad_group = restapi.access.get_ad_group(request.user, ad_group_id)
        self._augment_ad_group(request, ad_group)
        extra_data = helpers.get_extra_data(request.user, ad_group)
        return self.response_ok(
            data=self.serializer(ad_group.settings, context={"request": request}).data,
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
        serializer = self.serializer(data=request.data, partial=True, context={"request": request})
        serializer.is_valid(raise_exception=True)
        settings = serializer.validated_data

        with transaction.atomic():
            self._handle_update_create_exceptions(
                settings, self._update_settings, request, ad_group, serializer.validated_data
            )
            if "deals" in settings.keys():
                self._handle_deals(request, ad_group, settings.get("deals", []))

        self._augment_ad_group(request, ad_group)
        return self.response_ok(self.serializer(ad_group.settings, context={"request": request}).data)

    def create(self, request):
        serializer = self.serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        settings = serializer.validated_data
        campaign = restapi.access.get_campaign(request.user, settings.get("ad_group", {}).get("campaign_id"))

        with transaction.atomic():
            try:
                new_ad_group = core.models.AdGroup.objects.create(
                    request, campaign=campaign, name=settings.get("ad_group_name", None), is_restapi=True
                )

            except core.models.ad_group.exceptions.CampaignIsArchived as err:
                raise utils.exc.ValidationError(errors={"campaign_id": [str(err)]})

            self._handle_update_create_exceptions(settings, self._update_settings, request, new_ad_group, settings)

            self._handle_deals(request, new_ad_group, settings.get("deals", []))
            prodops.hacks.apply_ad_group_create_hacks(request, new_ad_group)

        self._augment_ad_group(request, new_ad_group)
        return self.response_ok(self.serializer(new_ad_group.settings, context={"request": request}).data, status=201)

    @staticmethod
    def _augment_ad_group(request, ad_group):
        ad_group.settings.deals = []
        if request.user.has_perm("zemauth.can_see_direct_deals_section"):
            ad_group.settings.deals = ad_group.get_deals()

    @staticmethod
    def _handle_deals(request, ad_group, data):
        errors = []
        new_deals = []

        for item in data:
            if item.get("id") is not None:
                try:
                    new_deals.append(restapi.access.get_direct_deal(request.user, item.get("id")))
                    errors.append(None)
                except utils.exc.MissingDataError as err:
                    errors.append({"id": [str(err)]})
            else:
                new_deal = core.features.deals.DirectDeal.objects.create(
                    request,
                    agency=ad_group.campaign.account.agency,
                    source=item.get("source"),
                    deal_id=item.get("deal_id"),
                    name=item.get("name"),
                )
                new_deal.update(request, **item)
                new_deals.append(new_deal)
                errors.append(None)

        if any([error is not None for error in errors]):
            raise utils.exc.ValidationError(errors={"deals": errors})

        new_deals_set = set(new_deals)

        deals = ad_group.get_deals()
        deals_set = set(deals)

        to_be_removed = deals_set.difference(new_deals_set)
        to_be_added = new_deals_set.difference(deals_set)

        if to_be_removed or to_be_added:
            ad_group.remove_deals(request, list(to_be_removed))
            ad_group.add_deals(request, list(to_be_added))
