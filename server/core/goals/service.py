import decimal

import dash.constants
import core.multicurrency
import utils.numbers

import dash.campaign_goals

_CAMPAIGN_GOAL_DEFAULT_VALUE = {
    dash.constants.CampaignGoalKPI.TIME_ON_SITE: {"value": decimal.Decimal("30.0")},
    dash.constants.CampaignGoalKPI.MAX_BOUNCE_RATE: {"value": decimal.Decimal("75.0")},
    dash.constants.CampaignGoalKPI.NEW_UNIQUE_VISITORS: {"value": decimal.Decimal("85.0")},
    dash.constants.CampaignGoalKPI.PAGES_PER_SESSION: {"value": decimal.Decimal("1.2")},
    dash.constants.CampaignGoalKPI.CPA: {"value": decimal.Decimal("50"), "convert_to_local": True},
    dash.constants.CampaignGoalKPI.CPC: {"value": decimal.Decimal("0.35"), "convert_to_local": True},
    dash.constants.CampaignGoalKPI.CPV: {"value": decimal.Decimal("0.5"), "convert_to_local": True},
    dash.constants.CampaignGoalKPI.CP_NON_BOUNCED_VISIT: {"value": decimal.Decimal("2.8"), "convert_to_local": True},
    dash.constants.CampaignGoalKPI.CP_NEW_VISITOR: {"value": decimal.Decimal("2.8"), "convert_to_local": True},
    dash.constants.CampaignGoalKPI.CP_PAGE_VIEW: {"value": decimal.Decimal("0.45"), "convert_to_local": True},
    dash.constants.CampaignGoalKPI.CPCV: {"value": decimal.Decimal("0.6"), "convert_to_local": True},
}


def get_campaign_goals_defaults(account):
    exchange_rate = core.multicurrency.get_current_exchange_rate(account.currency)
    return {
        kpi: _convert_to_local_value(kpi, value, exchange_rate) for kpi, value in _CAMPAIGN_GOAL_DEFAULT_VALUE.items()
    }


def _convert_to_local_value(kpi, value, exchange_rate):
    converted_value = value.get("value")

    if value.get("convert_to_local"):
        converted_value = utils.numbers.round_to_significant_figures(converted_value * exchange_rate, 2)

    return dash.campaign_goals.CAMPAIGN_GOAL_VALUE_FORMAT[kpi](converted_value, curr="")
