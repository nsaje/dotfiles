from rest_framework import permissions
from django.db import transaction

from restapi.common.views_base import RESTAPIBaseViewSet
from restapi.campaigngoal.serializers import CampaignGoalsDefaultsSerializer
import restapi.serializers.targeting
import restapi.access
import dash.features.campaignlauncher
import dash.features.contentupload
import core.models.settings
import core.multicurrency
import automation.autopilot
import utils.lc_helper
import utils.exc

from . import serializers


BUDGET_DAILY_CAP_FACTOR = 3


class CampaignLauncherViewSet(RESTAPIBaseViewSet):
    permission_classes = (permissions.IsAuthenticated,)

    def defaults(self, request, account_id):
        account = restapi.access.get_account(request.user, account_id)
        default_settings = core.models.settings.AdGroupSettings.get_defaults_dict()
        return self.response_ok(
            {
                "target_regions": restapi.serializers.targeting.TargetRegionsSerializer(
                    default_settings["target_regions"]
                ).data,
                "exclusion_target_regions": restapi.serializers.targeting.TargetRegionsSerializer(
                    default_settings["exclusion_target_regions"]
                ).data,
                "target_devices": restapi.serializers.targeting.DevicesSerializer(
                    default_settings["target_devices"]
                ).data,
                "goals_defaults": CampaignGoalsDefaultsSerializer(core.goals.get_campaign_goals_defaults(account)).data,
            }
        )

    def validate(self, request, account_id):
        account = restapi.access.get_account(request.user, account_id)
        serializer = serializers.CampaignLauncherSerializer(
            data=request.data, context={"account": account}, partial=True
        )
        serializer.is_valid()
        errors = serializer.errors
        if "upload_batch" in serializer.validated_data:
            upload_batch = restapi.access.get_upload_batch(request.user, serializer.validated_data["upload_batch"])
            try:
                dash.features.contentupload.upload.clean_candidates(upload_batch)
            except Exception as e:
                errors["upload_batch"] = e
        if "daily_budget" in serializer.validated_data and "budget_amount" in serializer.validated_data:
            currency_symbol = core.multicurrency.get_currency_symbol(account.currency)
            exchange_rate = core.multicurrency.get_current_exchange_rate(account.currency)
            min_daily_budget = automation.autopilot.get_account_default_minimum_daily_budget(account) * exchange_rate
            min_budget_amount = min_daily_budget * BUDGET_DAILY_CAP_FACTOR
            if serializer.validated_data["daily_budget"] < min_daily_budget:
                errors["daily_budget"] = [
                    "Should be at least {}".format(
                        utils.lc_helper.format_currency(min_daily_budget, places=0, curr=currency_symbol)
                    )
                ]
            if serializer.validated_data["budget_amount"] < min_budget_amount:
                errors["budget_amount"] = [
                    "Should be at least {}".format(
                        utils.lc_helper.format_currency(min_budget_amount, places=0, curr=currency_symbol)
                    )
                ]
        if errors:
            raise utils.exc.ValidationError(errors=errors)
        return self.response_ok(None)

    @transaction.atomic
    def launch(self, request, account_id):
        account = restapi.access.get_account(request.user, account_id)

        serializer = serializers.CampaignLauncherSerializer(data=request.data, context={"account": account})
        serializer.is_valid(raise_exception=True)

        upload_batch = restapi.access.get_upload_batch(request.user, serializer.validated_data["upload_batch"])

        campaign = dash.features.campaignlauncher.launch(
            request=request,
            account=account,
            name=serializer.validated_data["campaign_name"],
            iab_category=serializer.validated_data["iab_category"],
            language=serializer.validated_data["language"],
            type=serializer.validated_data["type"],
            budget_amount=serializer.validated_data["budget_amount"],
            max_cpc=serializer.validated_data["max_cpc"],
            daily_budget=serializer.validated_data["daily_budget"],
            upload_batch=upload_batch,
            goal_type=serializer.validated_data["campaign_goal"]["type"],
            goal_value=serializer.validated_data["campaign_goal"]["value"],
            target_regions=serializer.validated_data["target_regions"],
            exclusion_target_regions=serializer.validated_data["exclusion_target_regions"],
            target_devices=serializer.validated_data["target_devices"],
            target_placements=serializer.validated_data["target_placements"],
            target_os=serializer.validated_data["target_os"],
            conversion_goal_type=serializer.validated_data["campaign_goal"].get("conversion_goal", {}).get("type"),
            conversion_goal_goal_id=serializer.validated_data["campaign_goal"]
            .get("conversion_goal", {})
            .get("goal_id"),
            conversion_goal_window=serializer.validated_data["campaign_goal"]
            .get("conversion_goal", {})
            .get("conversion_window"),
        )

        return self.response_ok({"campaignId": campaign.id})
