from utils.constant_base import ConstantBase


class DailyBudgetChangeComment(ConstantBase):
    NO_ACTIVE_AD_GROUPS_WITH_SPEND = 1
    NEW_BUDGET_NOT_EQUAL_DAILY_BUDGET = 2
    USED_UP_BUDGET_THEN_UNIFORMLY_REDISTRIBUTED = 4

    _VALUES = {
        NO_ACTIVE_AD_GROUPS_WITH_SPEND: "Campaign does not have any active ad groups with enough spend."
        + " Budget was uniformly redistributed.",
        NEW_BUDGET_NOT_EQUAL_DAILY_BUDGET: "Budget Autopilot tried assigning wrong ammount of total daily spend caps.",
        USED_UP_BUDGET_THEN_UNIFORMLY_REDISTRIBUTED: "Used up all smart budget, then uniformly redistributed remaining.",
    }
