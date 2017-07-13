import rest_framework.serializers

from ..views import RESTAPIBaseViewSet
import restapi.access
import dash.features.campaignlauncher
import dash.features.contentupload

import serializers


class CampaignLauncherViewSet(RESTAPIBaseViewSet):

    def validate(self, request, account_id):
        serializer = serializers.CampaignLauncherSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        if 'upload_batch_id' in serializer.validated_data:
            upload_batch = restapi.access.get_upload_batch(request.user, serializer.validated_data['upload_batch_id'])
            try:
                dash.features.contentupload.upload.clean_candidates(upload_batch)
            except Exception as e:
                raise rest_framework.serializers.ValidationError(e)
        return self.response_ok(None)

    def launch(self, request, account_id):
        account = restapi.access.get_account(request.user, account_id)

        serializer = serializers.CampaignLauncherSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        upload_batch = restapi.access.get_upload_batch(request.user, serializer.validated_data['upload_batch_id'])

        campaign = dash.features.campaignlauncher.launch(
            request=request,
            account=account,
            name=serializer.validated_data['campaign_name'],
            iab_category=serializer.validated_data['iab_category'],
            start_date=serializer.validated_data['start_date'],
            end_date=serializer.validated_data['end_date'],
            budget_amount=serializer.validated_data['budget_amount'],
            max_cpc=serializer.validated_data['max_cpc'],
            daily_budget=serializer.validated_data['daily_budget'],
            upload_batch=upload_batch,
            goal_type=serializer.validated_data['campaign_goal']['type'],
            goal_value=serializer.validated_data['campaign_goal']['value'],
            conversion_goal_type=serializer.validated_data['campaign_goal']['conversion_goal']['type'],
            conversion_goal_goal_id=serializer.validated_data['campaign_goal']['conversion_goal']['goal_id'],
            conversion_goal_window=serializer.validated_data['campaign_goal']['conversion_goal']['conversion_window'],
        )

        return self.response_ok({'campaignId': campaign.id})
