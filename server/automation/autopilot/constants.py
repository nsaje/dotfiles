from utils.constant_base import ConstantBase
import dash.constants


class BidChangeComment(ConstantBase):
    BUDGET_MANUALLY_CHANGED = 1
    NO_YESTERDAY_SPEND = 2
    HIGH_OVERSPEND = 3
    OLD_DATA = 4
    OPTIMAL_SPEND = 5
    BUDGET_NOT_SET = 6
    BID_NOT_SET = 7
    CURRENT_BID_TOO_HIGH = 8
    CURRENT_BID_TOO_LOW = 9
    OVER_SOURCE_MAX_BID = 10
    UNDER_SOURCE_MIN_BID = 11
    OVER_AD_GROUP_MAX_BID = 12
    OVER_AUTOPILOT_MAX_BID = 13
    UNDER_AUTOPILOT_MIN_BID = 14
    OVER_ACCOUNT_SOURCE_MIN_BID = 15  # deprecated
    UNDER_ACCOUNT_SOURCE_MIN_BID = 16  # deprecated
    OVER_AD_GROUP_SOURCE_MIN_BID = 17  # deprecated
    UNDER_AD_GROUP_SOURCE_MIN_BID = 18  # deprecated
    BID_CONSTRAINT_APPLIED = 19

    _VALUES = {
        BUDGET_MANUALLY_CHANGED: "budget was manually changed recently",
        NO_YESTERDAY_SPEND: "there was no spend yesterday",
        HIGH_OVERSPEND: "media source overspent significantly considering current daily spend cap",
        OLD_DATA: "latest data was not available",
        OPTIMAL_SPEND: "it is running at optimal price for given budget",
        BUDGET_NOT_SET: "daily spend cap was not set",
        BID_NOT_SET: "bid {bid} was not set",
        CURRENT_BID_TOO_HIGH: "Autopilot can not operate on higher {bid}",
        CURRENT_BID_TOO_LOW: "Autopilot can not operate on lower {bid}",
        OVER_SOURCE_MAX_BID: "higher bid {bid} would exceed media source's {bid} constraint",
        UNDER_SOURCE_MIN_BID: "lower bid {bid} would not meet media source's minimum {bid} constraint",
        OVER_AD_GROUP_MAX_BID: "higher bid {bid} would exceed ad group's maximum {bid} constraint",
        OVER_AUTOPILOT_MAX_BID: "higher bid {bid} would exceed Autopilot's maximum allowed {bid} constraint",
        UNDER_AUTOPILOT_MIN_BID: "lower bid {bid} would not meet Autopilot's minimum allowed {bid} constraint",
        OVER_ACCOUNT_SOURCE_MIN_BID: "higher bid {bid} would not meet Account-Source specific {bid} constraint",
        UNDER_ACCOUNT_SOURCE_MIN_BID: "lower bid {bid} would not meet Account-Source specific {bid} constraint",
        OVER_AD_GROUP_SOURCE_MIN_BID: "higher bid {bid} would not meet Ad Group-Source specific {bid} constraint",
        UNDER_AD_GROUP_SOURCE_MIN_BID: "lower bid {bid} would not meet Ad Group-Source specific {bid} constraint",
        BID_CONSTRAINT_APPLIED: "bid {bid} had to be adjusted to meet applied {bid} constraints",
    }

    def get_text(self, constant, bidding_type=dash.constants.BiddingType.CPC):
        text = super().get_text(constant)
        return text.format(bid="CPM" if bidding_type == dash.constants.BiddingType.CPM else "CPC")


class DailyBudgetChangeComment(ConstantBase):
    NO_ACTIVE_SOURCES_WITH_SPEND = 1
    NEW_BUDGET_NOT_EQUAL_DAILY_BUDGET = 2
    INITIALIZE_PILOT_PAUSED_SOURCE = 3
    USED_UP_BUDGET_THEN_UNIFORMLY_REDISTRIBUTED = 4

    _VALUES = {
        NO_ACTIVE_SOURCES_WITH_SPEND: "Ad Group does not have any active sources with enough spend."
        + " Budget was uniformly redistributed.",
        NEW_BUDGET_NOT_EQUAL_DAILY_BUDGET: "Budget Autopilot tried assigning wrong ammount of total daily spend caps.",
        INITIALIZE_PILOT_PAUSED_SOURCE: "Budget Autopilot initialization - set paused source to minimum budget.",
        USED_UP_BUDGET_THEN_UNIFORMLY_REDISTRIBUTED: "Used up all smart budget, then uniformly redistributed remaining.",
    }
