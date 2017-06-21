from ..views import RESTAPIBaseViewSet
import restapi.access
from dash import models

import serializers


class CampaignLauncherViewSet(RESTAPIBaseViewSet):

    def validate(self, request, account_id):
        serializer = serializers.CampaignLauncherSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        return self.response_ok(None)

    def launch(self, request, account_id):
        account = restapi.access.get_account(request.user, account_id)

        serializer = serializers.CampaignLauncherSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        campaign = models.Campaign.objects.create(
            user=request.user,
            account=account,
            name=serializer.validated_data['campaign_name'],
            iab_category=serializer.validated_data['iab_category'],
        )

        return self.response_ok({'campaignId': campaign.id})
