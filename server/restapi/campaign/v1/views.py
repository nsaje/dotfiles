from django.db import transaction

import core.models
import prodops.hacks
import restapi.access
import utils.converters
import utils.exc
from restapi.common.pagination import StandardPagination
from restapi.common.views_base import RESTAPIBaseViewSet

from . import serializers


class CampaignViewSet(RESTAPIBaseViewSet):
    def get(self, request, campaign_id):
        campaign = restapi.access.get_campaign(request.user, campaign_id)
        return self.response_ok(serializers.CampaignSerializer(campaign.settings, context={"request": request}).data)

    def put(self, request, campaign_id):
        campaign = restapi.access.get_campaign(request.user, campaign_id)
        serializer = serializers.CampaignSerializer(data=request.data, partial=True, context={"request": request})
        serializer.is_valid(raise_exception=True)
        self._update_campaign(request, campaign, serializer.validated_data)
        return self.response_ok(serializers.CampaignSerializer(campaign.settings, context={"request": request}).data)

    def list(self, request):
        account_id = request.query_params.get("accountId", None)
        if account_id:
            account = restapi.access.get_account(request.user, account_id)
            campaigns = core.models.Campaign.objects.filter(account=account)
        else:
            campaigns = core.models.Campaign.objects.all().filter_by_user(request.user)

        if not utils.converters.x_to_bool(request.GET.get("includeArchived")):
            campaigns = campaigns.exclude_archived()

        campaigns = campaigns.select_related("settings").order_by("pk")
        paginator = StandardPagination()
        campaigns_paginated = paginator.paginate_queryset(campaigns, request)
        paginated_settings = [c.settings for c in campaigns_paginated]
        return paginator.get_paginated_response(
            serializers.CampaignSerializer(paginated_settings, many=True, context={"request": request}).data
        )

    def create(self, request):
        serializer = serializers.CampaignSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        settings = serializer.validated_data
        account = restapi.access.get_account(request.user, settings.get("campaign", {}).get("account_id"))

        with transaction.atomic():
            try:
                new_campaign = core.models.Campaign.objects.create(
                    request, account=account, name=settings.get("name"), type=settings.get("campaign", {}).get("type")
                )

            except core.models.campaign.exceptions.AccountIsArchived as err:
                raise utils.exc.ValidationError(errors={"account_id": [str(err)]})

            self._update_campaign(request, new_campaign, settings)
            prodops.hacks.apply_campaign_create_hacks(request, new_campaign)

        return self.response_ok(
            serializers.CampaignSerializer(new_campaign.settings, context={"request": request}).data, status=201
        )

    def _update_campaign(self, request, campaign, settings):
        try:
            settings = prodops.hacks.override_campaign_settings(campaign, settings)
            campaign.update_type(settings.get("campaign", {}).get("type"))
            campaign.settings.update(request, **settings)

        except core.models.settings.campaign_settings.exceptions.CannotChangeLanguage as err:
            raise utils.exc.ValidationError(errors={"language": [str(err)]})

        except core.models.campaign.exceptions.CannotChangeType as err:
            raise utils.exc.ValidationError(errors={"type": [str(err)]})

        except core.models.settings.campaign_settings.exceptions.PublisherWhitelistInvalid as err:
            raise utils.exc.ValidationError(errors={"targeting": {"publisherGroups": {"included": [str(err)]}}})

        except core.models.settings.campaign_settings.exceptions.PublisherBlacklistInvalid as err:
            raise utils.exc.ValidationError(errors={"targeting": {"publisherGroups": {"excluded": [str(err)]}}})
