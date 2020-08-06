import rest_framework.permissions
import rest_framework.serializers
from django.db import transaction
from rest_framework import permissions

import automation.campaignstop
import core.models
import core.models.ad_group.exceptions
import core.models.content_ad.exceptions
import dash.features.alerts
import dash.features.cloneadgroup
import dash.views.navigation_helpers
import prodops.hacks
import restapi.adgroup.v1.views
import restapi.serializers.alert
import utils.exc
import zemauth.access
from dash import constants
from restapi.common.pagination import StandardPagination
from restapi.common.views_base import RESTAPIBaseViewSet
from zemauth.features.entity_permission import Permission

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
        qpe = serializers.AdGroupInternalQueryParams(data=request.query_params)
        qpe.is_valid(raise_exception=True)
        campaign_id = qpe.validated_data.get("campaign_id")
        campaign = zemauth.access.get_campaign(request.user, Permission.WRITE, campaign_id)
        ad_group = core.models.AdGroup.objects.get_default(request, campaign)
        self._augment_ad_group(request, ad_group)
        extra_data = helpers.get_extra_data(request.user, ad_group)
        return self.response_ok(
            data=self.serializer(ad_group.settings, context={"request": request}).data,
            extra=serializers.ExtraDataSerializer(extra_data, context={"request": request}).data,
        )

    def get(self, request, ad_group_id):
        ad_group = zemauth.access.get_ad_group(request.user, Permission.READ, ad_group_id)
        self._augment_ad_group(request, ad_group)
        extra_data = helpers.get_extra_data(request.user, ad_group)
        return self.response_ok(
            data=self.serializer(ad_group.settings, context={"request": request}).data,
            extra=serializers.ExtraDataSerializer(extra_data, context={"request": request}).data,
        )

    def list(self, request):
        qpe = serializers.AdGroupListQueryParams(data=request.query_params)
        qpe.is_valid(raise_exception=True)

        account_id = qpe.validated_data.get("account_id")
        agency_id = qpe.validated_data.get("agency_id")

        if account_id:
            account = zemauth.access.get_account(request.user, Permission.READ, account_id)
            ad_group_qs = core.models.AdGroup.objects.filter(campaign__account=account)
        elif agency_id:
            agency = zemauth.access.get_agency(request.user, Permission.READ, agency_id)
            ad_group_qs = core.models.AdGroup.objects.filter(campaign__account__agency=agency)
        else:
            raise utils.exc.ValidationError("Either agency id or account id must be provided.")

        keyword = qpe.validated_data.get("keyword")
        if keyword:
            ad_group_qs = ad_group_qs.filter(name__icontains=keyword)

        paginator = StandardPagination()

        ad_group_qs = ad_group_qs.select_related("settings").order_by("pk")

        ad_groups_paginated = paginator.paginate_queryset(ad_group_qs, request)
        paginated_settings = [ad.settings for ad in ad_groups_paginated]
        return paginator.get_paginated_response(
            self.serializer(paginated_settings, many=True, context={"request": request}).data
        )

    def alerts(self, request, ad_group_id):
        qpe = restapi.serializers.alert.AlertQueryParams(data=request.query_params)
        qpe.is_valid(raise_exception=True)

        ad_group = zemauth.access.get_ad_group(request.user, Permission.READ, ad_group_id)
        alerts = dash.features.alerts.get_ad_group_alerts(request, ad_group, **qpe.validated_data)

        return self.response_ok(
            data=restapi.serializers.alert.AlertSerializer(alerts, many=True, context={"request": request}).data
        )

    def put(self, request, ad_group_id):
        ad_group = zemauth.access.get_ad_group(request.user, Permission.WRITE, ad_group_id)
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
        campaign = zemauth.access.get_campaign(
            request.user, Permission.WRITE, settings.get("ad_group", {}).get("campaign_id")
        )

        with transaction.atomic():
            try:
                new_ad_group = self._handle_update_create_exceptions(
                    settings,
                    core.models.AdGroup.objects.create,
                    request,
                    campaign=campaign,
                    name=settings.get("ad_group_name", None),
                    bidding_type=settings.get("ad_group", {}).get("bidding_type"),
                    is_restapi=True,
                    initial_settings=settings,
                )

            except core.models.ad_group.exceptions.CampaignIsArchived as err:
                raise utils.exc.ValidationError(errors={"campaign_id": [str(err)]})

            self._handle_deals(request, new_ad_group, settings.get("deals", []))
            prodops.hacks.apply_ad_group_create_hacks(request, new_ad_group)

        self._augment_ad_group(request, new_ad_group)
        return self.response_ok(self.serializer(new_ad_group.settings, context={"request": request}).data, status=201)

    @staticmethod
    def _augment_ad_group(request, ad_group):
        ad_group.settings.deals = []
        if request.user.has_perm("zemauth.can_see_direct_deals_section"):
            ad_group.settings.deals = ad_group.get_deals(request)

    @staticmethod
    def _handle_deals(request, ad_group, data):
        errors = []
        new_deals = []

        for item in data:
            if item.get("id") is not None:
                try:
                    deal = core.features.deals.DirectDeal.objects.filter(pk=item.get("id")).first()
                    if not deal:
                        raise utils.exc.MissingDataError("Deal does not exist")
                    if deal.agency_id and ad_group.campaign.account.agency_id != deal.agency_id:
                        raise utils.exc.MissingDataError("Deal does not exist")
                    if deal.account_id and ad_group.campaign.account_id != deal.account_id:
                        raise utils.exc.MissingDataError("Deal does not exist")
                    new_deals.append(deal)
                    errors.append(None)
                except utils.exc.MissingDataError as err:
                    errors.append({"id": [str(err)]})
            else:
                new_deal = core.features.deals.DirectDeal.objects.create(
                    request,
                    account=ad_group.campaign.account,
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

        deals = ad_group.get_deals(request)
        deals_set = set(deals)

        to_be_removed = deals_set.difference(new_deals_set)
        to_be_added = new_deals_set.difference(deals_set)

        if to_be_removed or to_be_added:
            ad_group.remove_deals(request, list(to_be_removed))
            ad_group.add_deals(request, list(to_be_added))


class CanUseCloneAdGroupsPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.has_perm("zemauth.can_clone_adgroups"))


class CloneAdGroupViewSet(RESTAPIBaseViewSet):
    permission_classes = (permissions.IsAuthenticated, CanUseCloneAdGroupsPermission)

    def post(self, request):
        serializer = serializers.CloneAdGroupSerializer(data=request.data, context=self.get_serializer_context())
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        try:
            ad_group = dash.features.cloneadgroup.service.clone(
                request,
                zemauth.access.get_ad_group(request.user, Permission.WRITE, validated_data["ad_group_id"]),
                zemauth.access.get_campaign(request.user, Permission.WRITE, validated_data["destination_campaign_id"]),
                validated_data["destination_ad_group_name"],
                validated_data["clone_ads"],
            )

        except (
            core.models.ad_group.exceptions.CampaignTypesDoNotMatch,
            core.models.content_ad.exceptions.CampaignAdTypeMismatch,
        ) as err:
            raise utils.exc.ValidationError(errors={"destination_campaign_id": [str(err)]})

        response = dash.views.navigation_helpers.get_ad_group_dict(
            request.user,
            ad_group.__dict__,
            ad_group.get_current_settings(),
            ad_group.campaign.get_current_settings(),
            automation.campaignstop.get_campaignstop_state(ad_group.campaign),
            real_time_campaign_stop=ad_group.campaign.real_time_campaign_stop,
        )

        response["campaign_id"] = ad_group.campaign_id
        return self.response_ok(serializers.CloneAdGroupResponseSerializer(response).data)
