import decimal

from rest_framework import fields
from rest_framework import serializers

import core.features.multicurrency
import dash.constants
import restapi.serializers.fields
import utils.lc_helper
from restapi.serializers import targeting


class ConversionGoalSerializer(serializers.Serializer):
    type = restapi.serializers.fields.DashConstantField(dash.constants.ConversionGoalType)
    conversion_window = restapi.serializers.fields.DashConstantField(dash.constants.ConversionWindows, required=False)
    goal_id = restapi.serializers.fields.PlainCharField(
        required=True,
        max_length=100,
        error_messages={"max_length": "Conversion goal id is too long (%(show_value)d/%(limit_value)d)."},
    )


class CampaignGoalSerializer(serializers.Serializer):
    type = restapi.serializers.fields.DashConstantField(dash.constants.CampaignGoalKPI)
    value = fields.DecimalField(max_digits=15, decimal_places=5, rounding=decimal.ROUND_HALF_DOWN)
    conversion_goal = ConversionGoalSerializer(required=False, allow_null=True)


class CampaignLauncherSerializer(serializers.Serializer):
    campaign_name = restapi.serializers.fields.PlainCharField(
        max_length=127, error_messages={"required": "Please specify campaign name."}
    )
    iab_category = restapi.serializers.fields.DashConstantField(
        dash.constants.IABCategory, error_messages={"required": "Please specify the IAB category."}
    )
    language = restapi.serializers.fields.DashConstantField(
        dash.constants.Language, error_messages={"required": "Please specify the language of the campaign's ads."}
    )
    type = restapi.serializers.fields.DashConstantField(
        dash.constants.CampaignType, error_messages={"required": "Please specify the type of the campaign."}
    )
    budget_amount = fields.IntegerField(min_value=0)
    max_cpc = fields.DecimalField(
        required=False, allow_null=True, max_digits=None, decimal_places=4, rounding=decimal.ROUND_HALF_DOWN
    )
    daily_budget = fields.DecimalField(max_digits=10, decimal_places=4, rounding=decimal.ROUND_HALF_DOWN)
    upload_batch = restapi.serializers.fields.IdField()
    campaign_goal = CampaignGoalSerializer()
    target_regions = targeting.TargetRegionsSerializer()
    exclusion_target_regions = targeting.TargetRegionsSerializer()
    target_devices = targeting.DevicesSerializer()
    target_placements = targeting.PlacementsSerializer()
    target_os = targeting.OSsSerializer()

    def validate_max_cpc(self, value):
        if not value:
            return value

        account = self.context["account"]
        currency_symbol = core.features.multicurrency.get_currency_symbol(account.currency)
        exchange_rate = core.features.multicurrency.get_current_exchange_rate(account.currency)
        min_cpc = round(decimal.Decimal("0.05") * exchange_rate, 3)
        max_cpc = round(decimal.Decimal("10") * exchange_rate, 3)

        if value < min_cpc:
            raise serializers.ValidationError(
                "Maximum CPC can't be lower than {}.".format(
                    utils.lc_helper.format_currency(min_cpc, places=3, curr=currency_symbol)
                )
            )
        if value > max_cpc:
            raise serializers.ValidationError(
                "Maximum CPC can't be higher than {}.".format(
                    utils.lc_helper.format_currency(max_cpc, places=3, curr=currency_symbol)
                )
            )

        return value
