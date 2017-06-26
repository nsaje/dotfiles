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
            request=request,
            account=account,
            name=serializer.validated_data['campaign_name'],
            iab_category=serializer.validated_data['iab_category'],
            start_date=serializer.validated_data['start_date'],
            end_date=serializer.validated_data['end_date'],
            budget_amount=serializer.validated_data['budget_amount'],
            goal_type=serializer.validated_data['goal']['type'],
            goal_value=serializer.validated_data['goal']['value'],
            conversion_goal_type=serializer.validated_data['goal']['conversion_goal']['type'],
            conversion_goal_goal_id=serializer.validated_data['goal']['conversion_goal']['goal_id'],
            conversion_goal_window=serializer.validated_data['goal']['conversion_goal']['conversion_window'],
        )

        return self.response_ok({'campaignId': campaign.id})
