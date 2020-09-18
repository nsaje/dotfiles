from django.db import transaction

import core.models
import prodops.hacks
import utils.converters
import utils.exc
import zemauth.access
from restapi.common.pagination import StandardPagination
from restapi.common.views_base import RESTAPIBaseViewSet
from zemauth.features.entity_permission import Permission

from . import serializers


class CampaignViewSet(RESTAPIBaseViewSet):
    serializer = serializers.CampaignSerializer

    def get(self, request, campaign_id):
        campaign = zemauth.access.get_campaign(request.user, Permission.READ, campaign_id)
        return self.response_ok(self.serializer(campaign.settings, context={"request": request}).data)

    def put(self, request, campaign_id):
        campaign = zemauth.access.get_campaign(request.user, Permission.WRITE, campaign_id)
        serializer = self.serializer(data=request.data, partial=True, context={"request": request})
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            self._update_campaign(request, campaign, serializer.validated_data)

        return self.response_ok(self.serializer(campaign.settings, context={"request": request}).data)

    def list(self, request):
        qpe = serializers.CampaignQueryParams(data=request.query_params)
        qpe.is_valid(raise_exception=True)

        account_id = qpe.validated_data.get("account_id", None)
        if account_id:
            account = zemauth.access.get_account(request.user, Permission.READ, account_id)
            campaigns = core.models.Campaign.objects.filter(account=account)
        else:
            campaigns = core.models.Campaign.objects.filter_by_entity_permission(request.user, Permission.READ)

        if not utils.converters.x_to_bool(request.GET.get("includeArchived")):
            campaigns = campaigns.exclude_archived()

        exclude_inactive = qpe.validated_data.get("exclude_inactive", False)
        if exclude_inactive:
            campaigns = campaigns.filter_has_active_ad_groups()

        paginator = StandardPagination()

        only_non_paginated_ids = qpe.validated_data.get("only_non_paginated_ids", False)
        if only_non_paginated_ids:
            campaigns = campaigns.order_by("id").values("id")
            return self.response_ok(
                serializers.CampaignIdsSerializer(campaigns, many=True, context={"request": request}).data
            )

        campaigns = campaigns.select_related("settings").order_by("pk")
        campaigns_paginated = paginator.paginate_queryset(campaigns, request)
        paginated_settings = [c.settings for c in campaigns_paginated]
        return paginator.get_paginated_response(
            self.serializer(paginated_settings, many=True, context={"request": request}).data
        )

    def create(self, request):
        serializer = self.serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        settings = serializer.validated_data
        account = zemauth.access.get_account(
            request.user, Permission.WRITE, settings.get("campaign", {}).get("account_id")
        )

        with transaction.atomic():
            try:
                new_campaign = core.models.Campaign.objects.create(
                    request, account=account, name=settings.get("name"), type=settings.get("campaign", {}).get("type")
                )

            except core.models.campaign.exceptions.AccountIsArchived as err:
                raise utils.exc.ValidationError(errors={"account_id": [str(err)]})

            self._update_campaign(request, new_campaign, settings)
            prodops.hacks.apply_campaign_create_hacks(request, new_campaign)

        return self.response_ok(self.serializer(new_campaign.settings, context={"request": request}).data, status=201)

    @staticmethod
    def _update_campaign(request, campaign, settings):
        try:
            settings = prodops.hacks.override_campaign_settings(campaign, settings)
            campaign.update_type(settings.get("campaign", {}).get("type"))
            campaign.settings.update(request, **settings)

        except core.models.campaign.exceptions.CannotChangeType as err:
            raise utils.exc.ValidationError(errors={"type": [str(err)]})

        except core.models.settings.campaign_settings.exceptions.PublisherWhitelistInvalid as err:
            raise utils.exc.ValidationError(errors={"targeting": {"publisherGroups": {"included": [str(err)]}}})

        except core.models.settings.campaign_settings.exceptions.PublisherBlacklistInvalid as err:
            raise utils.exc.ValidationError(errors={"targeting": {"publisherGroups": {"excluded": [str(err)]}}})
