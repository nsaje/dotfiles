from ..views import RESTAPIBaseViewSet
import restapi.access
import dash.features.campaignlauncher

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

        campaign = dash.features.campaignlauncher.launch(
            user=request.user,
            account=account,
            name=serializer.validated_data['campaign_name'],
            iab_category=serializer.validated_data['iab_category'],
            start_date=serializer.validated_data['start_date'],
            end_date=serializer.validated_data['end_date'],
            budget_amount=serializer.validated_data['budget_amount'],
        )

        return self.response_ok({'campaignId': campaign.id})
