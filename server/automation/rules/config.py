from dataclasses import dataclass

from core.features.bid_modifiers import MODIFIER_MAX
from core.features.bid_modifiers import MODIFIER_MIN

from . import constants


@dataclass
class AdjustmentTypeConfiguration:
    min_step: float
    max_step: float
    min_limit: float
    max_limit: float
    sign: str


VALID_ACTION_TYPES_FOR_TARGET = {
    constants.TargetType.AD_GROUP: [
        constants.ActionType.INCREASE_BID,
        constants.ActionType.DECREASE_BID,
        constants.ActionType.INCREASE_BUDGET,
        constants.ActionType.DECREASE_BUDGET,
        constants.ActionType.TURN_OFF,
        constants.ActionType.SEND_EMAIL,
    ],
    constants.TargetType.AD: [
        constants.ActionType.INCREASE_BID_MODIFIER,
        constants.ActionType.DECREASE_BID_MODIFIER,
        constants.ActionType.TURN_OFF,
    ],
    constants.TargetType.PUBLISHER: [
        constants.ActionType.INCREASE_BID_MODIFIER,
        constants.ActionType.DECREASE_BID_MODIFIER,
        constants.ActionType.BLACKLIST,
        constants.ActionType.ADD_TO_PUBLISHER_GROUP,
    ],
    constants.TargetType.DEVICE: [
        constants.ActionType.INCREASE_BID_MODIFIER,
        constants.ActionType.DECREASE_BID_MODIFIER,
    ],
    constants.TargetType.COUNTRY: [
        constants.ActionType.INCREASE_BID_MODIFIER,
        constants.ActionType.DECREASE_BID_MODIFIER,
    ],
    constants.TargetType.STATE: [
        constants.ActionType.INCREASE_BID_MODIFIER,
        constants.ActionType.DECREASE_BID_MODIFIER,
    ],
    constants.TargetType.DMA: [constants.ActionType.INCREASE_BID_MODIFIER, constants.ActionType.DECREASE_BID_MODIFIER],
    constants.TargetType.OS: [constants.ActionType.INCREASE_BID_MODIFIER, constants.ActionType.DECREASE_BID_MODIFIER],
    constants.TargetType.PLACEMENT: [
        constants.ActionType.INCREASE_BID_MODIFIER,
        constants.ActionType.DECREASE_BID_MODIFIER,
        # constants.ActionType.BLACKLIST,
    ],
    constants.TargetType.SOURCE: [
        constants.ActionType.INCREASE_BID_MODIFIER,
        constants.ActionType.DECREASE_BID_MODIFIER,
        constants.ActionType.TURN_OFF,
    ],
}

ADJUSTEMENT_ACTION_TYPES = {
    constants.ActionType.INCREASE_BID_MODIFIER: AdjustmentTypeConfiguration(
        min_limit=float(MODIFIER_MIN), max_limit=float(MODIFIER_MAX), min_step=0.01, max_step=1, sign="percentage"
    ),
    constants.ActionType.DECREASE_BID_MODIFIER: AdjustmentTypeConfiguration(
        min_limit=float(MODIFIER_MIN), max_limit=float(MODIFIER_MAX), min_step=0.01, max_step=1, sign="percentage"
    ),
    # TODO: Separate limits for CPC and CPM
    constants.ActionType.INCREASE_BID: AdjustmentTypeConfiguration(
        min_limit=0.01, max_limit=25, min_step=0.005, max_step=20, sign="currency"
    ),
    constants.ActionType.DECREASE_BID: AdjustmentTypeConfiguration(
        min_limit=0.01, max_limit=25, min_step=0.005, max_step=20, sign="currency"
    ),
    constants.ActionType.INCREASE_BUDGET: AdjustmentTypeConfiguration(
        min_limit=20, max_limit=100000, min_step=1, max_step=10000, sign="currency"
    ),
    constants.ActionType.DECREASE_BUDGET: AdjustmentTypeConfiguration(
        min_limit=20, max_limit=100000, min_step=1, max_step=10000, sign="currency"
    ),
}

VALID_LEFT_OPERAND_TYPES = {
    constants.MetricType.TOTAL_SPEND,
    constants.MetricType.IMPRESSIONS,
    constants.MetricType.CLICKS,
    constants.MetricType.CTR,
    constants.MetricType.AVG_CPC,
    constants.MetricType.AVG_CPM,
    constants.MetricType.VISITS,
    constants.MetricType.UNIQUE_USERS,
    constants.MetricType.NEW_USERS,
    constants.MetricType.RETURNING_USERS,
    constants.MetricType.NEW_USERS_RATIO,
    constants.MetricType.CLICK_DISCREPANCY,
    constants.MetricType.PAGEVIEWS,
    constants.MetricType.PAGEVIEWS_PER_VISIT,
    constants.MetricType.BOUNCED_VISITS,
    constants.MetricType.NON_BOUNCED_VISITS,
    constants.MetricType.BOUNCE_RATE,
    constants.MetricType.TOTAL_SECONDS,
    constants.MetricType.AVG_TIME_ON_SITE,
}

VALID_RIGTH_OPERAND_TYPES = {constants.ValueType.ABSOLUTE}

WINDOW_ADJUSTEMENT_POSSIBLE_TYPES = {
    constants.MetricType.TOTAL_SPEND,
    # constants.MetricType.AVG_DAILY_TOTAL_SPEND,  # TODO: add this metric
    constants.MetricType.IMPRESSIONS,
    constants.MetricType.CLICKS,
    constants.MetricType.CTR,
    constants.MetricType.AVG_CPC,
    constants.MetricType.AVG_CPM,
}

PERCENT_MODIFIER_LEFT_OPERAND_TYPES = {
    constants.MetricType.TOTAL_SPEND,
    # constants.MetricType.AVG_DAILY_TOTAL_SPEND,  # TODO: add metric
    constants.MetricType.IMPRESSIONS,
    constants.MetricType.CLICKS,
    constants.MetricType.CTR,
    constants.MetricType.AVG_CPC,
    constants.MetricType.AVG_CPM,
    constants.MetricType.VISITS,
    constants.MetricType.UNIQUE_USERS,
    constants.MetricType.NEW_USERS,
    constants.MetricType.RETURNING_USERS,
    constants.MetricType.NEW_USERS_RATIO,
    constants.MetricType.CLICK_DISCREPANCY,
    constants.MetricType.PAGEVIEWS,
    constants.MetricType.PAGEVIEWS_PER_VISIT,
    constants.MetricType.BOUNCED_VISITS,
    constants.MetricType.NON_BOUNCED_VISITS,
    constants.MetricType.BOUNCE_RATE,
    constants.MetricType.TOTAL_SECONDS,
    constants.MetricType.PRIMARY_GOAL,
    constants.MetricType.AD_GROUP_DAILY_CAP,
}

PERCENT_MODIFIER_RIGHT_OPERAND_TYPES = {
    constants.ValueType.CAMPAIGN_BUDGET,
    constants.ValueType.REMAINING_CAMPAIGN_BUDGET,
    constants.ValueType.AD_GROUP_DAILY_CAP,
    constants.ValueType.AD_GROUP_CLICK_DAILY_CAP,
}

DAY_MODIFIER_LEFT_OPERAND_TYPES = set(
    {
        # constants.MetricType.CONTENT_AD_CREATED_DATE,  # TODO: add metric
    }
)

DAY_MODIFIER_RIGHT_OPERAND_TYPES = {constants.ValueType.CURRENT_DATE}

EMAIL_ACTION_SETTINGS_MACROS = {
    constants.EmailActionMacro.AGENCY_ID,
    constants.EmailActionMacro.AGENCY_NAME,
    constants.EmailActionMacro.ACCOUNT_ID,
    constants.EmailActionMacro.ACCOUNT_NAME,
    constants.EmailActionMacro.CAMPAIGN_ID,
    constants.EmailActionMacro.CAMPAIGN_NAME,
    constants.EmailActionMacro.AD_GROUP_ID,
    constants.EmailActionMacro.AD_GROUP_NAME,
    constants.EmailActionMacro.AD_GROUP_DAILY_CAP,
    constants.EmailActionMacro.CAMPAIGN_BUDGET,
}

EMAIL_ACTION_STATS_MACROS = {
    constants.EmailActionMacro.TOTAL_SPEND,
    constants.EmailActionMacro.CLICKS,
    constants.EmailActionMacro.IMPRESSIONS,
    constants.EmailActionMacro.AVG_CPC,
    constants.EmailActionMacro.AVG_CPM,
    constants.EmailActionMacro.VISITS,
    constants.EmailActionMacro.UNIQUE_USERS,
    constants.EmailActionMacro.NEW_USERS,
    constants.EmailActionMacro.RETURNING_USERS,
    constants.EmailActionMacro.PERCENT_NEW_USERS,
    constants.EmailActionMacro.CLICK_DISCREPANCY,
    constants.EmailActionMacro.PAGEVIEWS,
    constants.EmailActionMacro.PAGEVIEWS_PER_VISIT,
    constants.EmailActionMacro.BOUNCED_VISITS,
    constants.EmailActionMacro.NON_BOUNCED_VISITS,
    constants.EmailActionMacro.BOUNCE_RATE,
    constants.EmailActionMacro.TOTAL_SECONDS,
    constants.EmailActionMacro.AVG_TIME_ON_SITE,
    constants.EmailActionMacro.AVG_COST_PER_VISIT,
    constants.EmailActionMacro.AVG_COST_PER_NEW_VISITOR,
    constants.EmailActionMacro.AVG_COST_PER_PAGEVIEW,
    constants.EmailActionMacro.AVG_COST_PER_NON_BOUNCED_VISIT,
    constants.EmailActionMacro.AVG_COST_PER_MINUTE,
}

EMAIL_ACTION_MACROS_VALID_WINDOWS = {
    constants.MetricWindow.LAST_DAY,
    constants.MetricWindow.LAST_3_DAYS,
    constants.MetricWindow.LAST_7_DAYS,
    constants.MetricWindow.LAST_30_DAYS,
}
