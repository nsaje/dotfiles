from utils.constant_base import ConstantBase


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
    OVER_ACCOUNT_SOURCE_MIN_CPC = 15
    UNDER_ACCOUNT_SOURCE_MIN_CPC = 16
    OVER_AD_GROUP_SOURCE_MIN_CPC = 17
    UNDER_AD_GROUP_SOURCE_MIN_CPC = 18

    _VALUES = {
        BUDGET_MANUALLY_CHANGED: 'budget was manually changed recently',
        NO_YESTERDAY_SPEND: 'there was no spend yesterday',
        HIGH_OVERSPEND: 'media source overspent significantly considering current daily spend cap',
        OLD_DATA: 'latest data was not available',
        OPTIMAL_SPEND: 'it is running at optimal price for given budget',
        BUDGET_NOT_SET: 'daily spend cap was not set',
        CPC_NOT_SET: 'bid CPC was not set',
        CURRENT_CPC_TOO_HIGH: 'Autopilot can not operate on higher CPC',
        CURRENT_CPC_TOO_LOW: 'Autopilot can not operate on lower CPC',
        OVER_SOURCE_MAX_CPC: 'higher bid CPC would exceed media source\'s CPC constraint',
        UNDER_SOURCE_MIN_CPC: 'lower bid CPC would not meet media source\'s minimum CPC constraint',
        OVER_AD_GROUP_MAX_CPC: 'higher bid CPC would exceed ad group\'s maximum CPC constraint',
        OVER_AUTOPILOT_MAX_CPC: 'higher bid CPC would exceed Autopilot\'s maximum allowed CPC constraint',
        UNDER_AUTOPILOT_MIN_CPC: 'lower bid CPC would not meet Autopilot\'s minimum allowed CPC constraint',
        OVER_ACCOUNT_SOURCE_MIN_CPC: 'higher bid CPC would not meet Account-Source specific CPC constraint',
        UNDER_ACCOUNT_SOURCE_MIN_CPC: 'lower bid CPC would not meet Account-Source specific CPC constraint',
        OVER_AD_GROUP_SOURCE_MIN_CPC: 'higher bid CPC would not meet Ad Group-Source specific CPC constraint',
        UNDER_AD_GROUP_SOURCE_MIN_CPC: 'lower bid CPC would not meet Ad Group-Source specific CPC constraint',
    }


class DailyBudgetChangeComment(ConstantBase):
    NO_ACTIVE_SOURCES_WITH_SPEND = 1
    NEW_BUDGET_NOT_EQUAL_DAILY_BUDGET = 2
    INITIALIZE_PILOT_PAUSED_SOURCE = 3
    USED_UP_BUDGET_THEN_UNIFORMLY_REDISTRIBUTED = 4

    _VALUES = {
        NO_ACTIVE_SOURCES_WITH_SPEND: 'Ad Group does not have any active sources with enough spend.' +
                                      ' Budget was uniformly redistributed.',
        NEW_BUDGET_NOT_EQUAL_DAILY_BUDGET: 'Budget Autopilot tried assigning wrong ammount of total daily spend caps.',
        INITIALIZE_PILOT_PAUSED_SOURCE: 'Budget Autopilot initialization - set paused source to minimum budget.',
        USED_UP_BUDGET_THEN_UNIFORMLY_REDISTRIBUTED: 'Used up all smart budget, then uniformly redistributed remaining.'
    }
