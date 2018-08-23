from restapi.common.views_base import RESTAPIBaseViewSet
from restapi.common.pagination import StandardPagination
import restapi.access

from django.db import transaction

import core.entity
import utils.exc
from . import serializers


class CampaignViewSet(RESTAPIBaseViewSet):
    def get(self, request, campaign_id):
        campaign = restapi.access.get_campaign(request.user, campaign_id)
        return self.response_ok(serializers.CampaignSerializer(campaign.settings).data)

    def put(self, request, campaign_id):
        campaign = restapi.access.get_campaign(request.user, campaign_id)
        serializer = serializers.CampaignSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self._update_campaign(request, campaign, serializer.validated_data)
        return self.response_ok(serializers.CampaignSerializer(campaign.settings).data)

    def list(self, request):
        account_id = request.query_params.get("accountId", None)
        if account_id:
            account = restapi.access.get_account(request.user, account_id)
            campaigns = core.entity.Campaign.objects.filter(account=account)
        else:
            campaigns = core.entity.Campaign.objects.all().filter_by_user(request.user)

        campaigns = campaigns.select_related("settings").order_by("pk")
        paginator = StandardPagination()
        campaigns_paginated = paginator.paginate_queryset(campaigns, request)
        paginated_settings = [c.settings for c in campaigns_paginated]
        return paginator.get_paginated_response(serializers.CampaignSerializer(paginated_settings, many=True).data)

    def create(self, request):
        serializer = serializers.CampaignSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        settings = serializer.validated_data
        account = restapi.access.get_account(request.user, settings.get("campaign", {}).get("account_id"))

        with transaction.atomic():
            new_campaign = core.entity.Campaign.objects.create(
                request, account=account, name=settings.get("name"), type=settings.get("campaign", {}).get("type")
            )
            self._update_campaign(request, new_campaign, settings)

        return self.response_ok(serializers.CampaignSerializer(new_campaign.settings).data, status=201)

    def _update_campaign(self, request, campaign, data):
        try:
            campaign.settings.update(request, **data)
            campaign.update_type(data.get("campaign", {}).get("type"))

        except core.entity.settings.campaign_settings.exceptions.CannotChangeLanguage as err:
            raise utils.exc.ValidationError(errors={"language": [str(err)]})

        except core.entity.campaign.exceptions.CannotChangeType as err:
            raise utils.exc.ValidationError(errors={"type": [str(err)]})

        except core.entity.settings.campaign_settings.exceptions.PublisherWhitelistInvalid as err:
            raise utils.exc.ValidationError(errors={"targeting": {"publisherGroups": {"included": [str(err)]}}})

        except core.entity.settings.campaign_settings.exceptions.PublisherBlacklistInvalid as err:
            raise utils.exc.ValidationError(errors={"targeting": {"publisherGroups": {"excluded": [str(err)]}}})
