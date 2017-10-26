import rest_framework.serializers
from rest_framework import permissions
from django.db import transaction

from ..views import RESTAPIBaseViewSet
import restapi.serializers.targeting
import restapi.access
import dash.features.campaignlauncher
import dash.features.contentupload
import core.entity.settings
import automation.autopilot_budgets

import serializers


BUDGET_DAILY_CAP_FACTOR = 3


class CampaignLauncherViewSet(RESTAPIBaseViewSet):
    permission_classes = (permissions.IsAuthenticated,)

    def defaults(self, request, account_id):
        default_settings = core.entity.settings.AdGroupSettings.get_defaults_dict()
        return self.response_ok({
            'target_regions': restapi.serializers.targeting.TargetRegionsSerializer(default_settings['target_regions']).data,
            'exclusion_target_regions': restapi.serializers.targeting.TargetRegionsSerializer(default_settings['exclusion_target_regions']).data,
            'target_devices': restapi.serializers.targeting.DevicesSerializer(default_settings['target_devices']).data,
        })

    def validate(self, request, account_id):
        account = restapi.access.get_account(request.user, account_id)
        serializer = serializers.CampaignLauncherSerializer(data=request.data, partial=True)
        serializer.is_valid()
        errors = serializer.errors
        if 'upload_batch' in serializer.validated_data:
            upload_batch = restapi.access.get_upload_batch(request.user, serializer.validated_data['upload_batch'])
            try:
                dash.features.contentupload.upload.clean_candidates(upload_batch)
            except Exception as e:
                errors['upload_batch'] = e
        if 'daily_budget' in serializer.validated_data and 'budget_amount' in serializer.validated_data:
            min_daily_budget = automation.autopilot_budgets.get_account_default_minimum_daily_budget(account)
            if serializer.validated_data['daily_budget'] < min_daily_budget:
                errors['daily_budget'] = ['Should be at least $%s' % min_daily_budget]
            if serializer.validated_data['budget_amount'] < min_daily_budget * BUDGET_DAILY_CAP_FACTOR:
                errors['budget_amount'] = ['Should be at least $%s' % (min_daily_budget * BUDGET_DAILY_CAP_FACTOR)]
        if errors:
            raise rest_framework.serializers.ValidationError(errors)
        return self.response_ok(None)

    @transaction.atomic
    def launch(self, request, account_id):
        account = restapi.access.get_account(request.user, account_id)

        serializer = serializers.CampaignLauncherSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        upload_batch = restapi.access.get_upload_batch(request.user, serializer.validated_data['upload_batch'])

        campaign = dash.features.campaignlauncher.launch(
            request=request,
            account=account,
            name=serializer.validated_data['campaign_name'],
            iab_category=serializer.validated_data['iab_category'],
            budget_amount=serializer.validated_data['budget_amount'],
            max_cpc=serializer.validated_data['max_cpc'],
            daily_budget=serializer.validated_data['daily_budget'],
            upload_batch=upload_batch,
            goal_type=serializer.validated_data['campaign_goal']['type'],
            goal_value=serializer.validated_data['campaign_goal']['value'],
            target_regions=serializer.validated_data['target_regions'],
            exclusion_target_regions=serializer.validated_data['exclusion_target_regions'],
            target_devices=serializer.validated_data['target_devices'],
            target_placements=serializer.validated_data['target_placements'],
            target_os=serializer.validated_data['target_os'],
            conversion_goal_type=serializer.validated_data['campaign_goal'].get('conversion_goal', {}).get('type'),
            conversion_goal_goal_id=serializer.validated_data['campaign_goal'].get('conversion_goal', {}).get('goal_id'),
            conversion_goal_window=serializer.validated_data['campaign_goal'].get('conversion_goal', {}).get('conversion_window'),
        )

        return self.response_ok({'campaignId': campaign.id})
