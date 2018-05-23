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
        settings_updates = serializer.validated_data
        if settings_updates:
            try:
                campaign.settings.update(request, **settings_updates)
            except core.entity.settings.campaign_settings.exceptions.CannotChangeLanguage as err:
                raise utils.exc.ValidationError(errors={
                    'language': str(err)
                })
        return self.response_ok(serializers.CampaignSerializer(campaign.settings).data)

    def list(self, request):
        account_id = request.query_params.get('accountId', None)
        if account_id:
            account = restapi.access.get_account(request.user, account_id)
            campaigns = core.entity.Campaign.objects.filter(account=account)
        else:
            campaigns = core.entity.Campaign.objects.all().filter_by_user(request.user)

        campaigns = campaigns.select_related('settings').order_by('pk')
        paginator = StandardPagination()
        campaigns_paginated = paginator.paginate_queryset(campaigns, request)
        paginated_settings = [c.settings for c in campaigns_paginated]
        return paginator.get_paginated_response(serializers.CampaignSerializer(paginated_settings, many=True).data)

    def create(self, request):
        serializer = serializers.CampaignSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        settings = serializer.validated_data
        account = restapi.access.get_account(request.user, settings['campaign']['account_id'])

        with transaction.atomic():
            new_campaign = core.entity.Campaign.objects.create(
                request,
                account=account,
                name=settings['name'],
            )
            new_campaign.settings.update(request, **settings)

        return self.response_ok(serializers.CampaignSerializer(new_campaign.settings).data, status=201)
