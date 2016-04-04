from utils.constant_base import ConstantBase
from dash.constants import CampaignGoalKPI


class CpcChangeComment(ConstantBase):
    BUDGET_MANUALLY_CHANGED = 1
    NO_YESTERDAY_SPEND = 2
    HIGH_OVERSPEND = 3
    OLD_DATA = 4
    OPTIMAL_SPEND = 5
    BUDGET_NOT_SET = 6
    CPC_NOT_SET = 7
    CURRENT_CPC_TOO_HIGH = 8
    CURRENT_CPC_TOO_LOW = 9
    OVER_SOURCE_MAX_CPC = 10
    UNDER_SOURCE_MIN_CPC = 11
    OVER_AD_GROUP_MAX_CPC = 12
    OVER_AUTOPILOT_MAX_CPC = 13
    UNDER_AUTOPILOT_MIN_CPC = 14

    _VALUES = {
        BUDGET_MANUALLY_CHANGED: 'budget was manually changed recently',
        NO_YESTERDAY_SPEND: 'there was no spend yesterday',
        HIGH_OVERSPEND: 'media source overspent significantly considering current daily budget',
        OLD_DATA: 'latest data was not available',
        OPTIMAL_SPEND: 'it is running at optimal price for given budget',
        BUDGET_NOT_SET: 'daily budget was not set',
        CPC_NOT_SET: 'bid CPC was not set',
        CURRENT_CPC_TOO_HIGH: 'Auto-Pilot can not operate on higher CPC',
        CURRENT_CPC_TOO_LOW: 'Auto-Pilot can not operate on lower CPC',
        OVER_SOURCE_MAX_CPC: 'higher bid CPC would exceed media source\'s CPC constraint',
        UNDER_SOURCE_MIN_CPC: 'lower bid CPC would not meet media source\'s minimum CPC constraint',
        OVER_AD_GROUP_MAX_CPC: 'higher bid CPC would exceed ad group\'s maximum CPC constraint',
        OVER_AUTOPILOT_MAX_CPC: 'higher bid CPC would exceed Auto-Pilot\'s maximum allowed CPC constraint',
        UNDER_AUTOPILOT_MIN_CPC: 'lower bid CPC would not meet Auto-Pilot\'s minimum allowed CPC constraint'
    }


class DailyBudgetChangeComment(ConstantBase):
    NO_ACTIVE_SOURCES_WITH_SPEND = 1
    NEW_BUDGET_NOT_EQUAL_DAILY_BUDGET = 2
    INITIALIZE_PILOT_PAUSED_SOURCE = 3

    _VALUES = {
        NO_ACTIVE_SOURCES_WITH_SPEND: 'Ad Group does not have any active sources with enough spend.' +
                                      ' Budget was uniformly redistributed.',
        NEW_BUDGET_NOT_EQUAL_DAILY_BUDGET: 'Budget Auto-Pilot tried assigning wrong ammount of total daily budgets',
        INITIALIZE_PILOT_PAUSED_SOURCE: 'Budget Auto-Pilot initialization - set paused source to minimum budget.'
    }


BudgetAutomationGoalText = {
    CampaignGoalKPI.TIME_ON_SITE: 'time on site',
    CampaignGoalKPI.MAX_BOUNCE_RATE: 'bounce rate',
    CampaignGoalKPI.PAGES_PER_SESSION: 'pages per session',
    CampaignGoalKPI.CPC: 'average CPC',
    CampaignGoalKPI.NEW_UNIQUE_VISITORS: 'new visitors',
}
