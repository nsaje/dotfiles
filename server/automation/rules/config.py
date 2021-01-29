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
    min_limit_error_message: str
    max_limit_error_message: str
    type: str


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
    constants.TargetType.ENVIRONMENT: [
        constants.ActionType.INCREASE_BID_MODIFIER,
        constants.ActionType.DECREASE_BID_MODIFIER,
        # constants.ActionType.BLACKLIST,
    ],
    constants.TargetType.SOURCE: [
        constants.ActionType.INCREASE_BID_MODIFIER,
        constants.ActionType.DECREASE_BID_MODIFIER,
        constants.ActionType.TURN_OFF,
    ],
    constants.TargetType.PLACEMENT: [
        constants.ActionType.INCREASE_BID_MODIFIER,
        constants.ActionType.DECREASE_BID_MODIFIER,
        constants.ActionType.BLACKLIST,
        constants.ActionType.ADD_TO_PUBLISHER_GROUP,
    ],
    constants.TargetType.BROWSER: [
        constants.ActionType.INCREASE_BID_MODIFIER,
        constants.ActionType.DECREASE_BID_MODIFIER,
    ],
    constants.TargetType.CONNECTION_TYPE: [
        constants.ActionType.INCREASE_BID_MODIFIER,
        constants.ActionType.DECREASE_BID_MODIFIER,
    ],
}

VALID_TARGET_TYPES_FOR_ACTION = {
    action_type: [
        target_type
        for target_type in constants.TargetType.get_all()
        if action_type in VALID_ACTION_TYPES_FOR_TARGET[target_type]
    ]
    for action_type in constants.ActionType.get_all()
}

ADJUSTMENT_ACTION_TYPE_PERCENTAGE = "percentage"
ADJUSTMENT_ACTION_TYPE_CURRENCY = "currency"

ADJUSTMENT_ACTION_TYPES = {
    constants.ActionType.INCREASE_BID_MODIFIER: AdjustmentTypeConfiguration(
        min_limit=float(MODIFIER_MIN),
        max_limit=float(MODIFIER_MAX),
        min_step=0.01,
        max_step=1,
        type=ADJUSTMENT_ACTION_TYPE_PERCENTAGE,
        min_limit_error_message="Maximum bid modifier must be {min_limit:.2f}{sign} or greater.",
        max_limit_error_message="Maximum bid modifier must be {max_limit:.2f}{sign} or less.",
    ),
    constants.ActionType.DECREASE_BID_MODIFIER: AdjustmentTypeConfiguration(
        min_limit=float(MODIFIER_MIN),
        max_limit=float(MODIFIER_MAX),
        min_step=0.01,
        max_step=1,
        type=ADJUSTMENT_ACTION_TYPE_PERCENTAGE,
        min_limit_error_message="Minimum bid modifier must be {min_limit:.2f}{sign} or greater.",
        max_limit_error_message="Minimum bid modifier must be {max_limit:.2f}{sign} or less.",
    ),
    # TODO: Separate limits for CPC and CPM
    constants.ActionType.INCREASE_BID: AdjustmentTypeConfiguration(
        min_limit=0.01,
        max_limit=25,
        min_step=0.005,
        max_step=20,
        type=ADJUSTMENT_ACTION_TYPE_CURRENCY,
        min_limit_error_message="Maximum bid must be {min_limit:.2f}{sign} or greater.",
        max_limit_error_message="Maximum bid must be {max_limit:.2f}{sign} or less.",
    ),
    constants.ActionType.DECREASE_BID: AdjustmentTypeConfiguration(
        min_limit=0.01,
        max_limit=25,
        min_step=0.005,
        max_step=20,
        type=ADJUSTMENT_ACTION_TYPE_CURRENCY,
        min_limit_error_message="Minimum bid must be {min_limit:.2f}{sign} or greater.",
        max_limit_error_message="Minimum bid must be {max_limit:.2f}{sign} or less.",
    ),
    constants.ActionType.INCREASE_BUDGET: AdjustmentTypeConfiguration(
        min_limit=20,
        max_limit=100000,
        min_step=1,
        max_step=10000,
        type=ADJUSTMENT_ACTION_TYPE_CURRENCY,
        min_limit_error_message="Maximum daily budget must be {min_limit:.2f}{sign} or greater.",
        max_limit_error_message="Maximum daily budget must be {max_limit:.2f}{sign} or less.",
    ),
    constants.ActionType.DECREASE_BUDGET: AdjustmentTypeConfiguration(
        min_limit=20,
        max_limit=100000,
        min_step=1,
        max_step=10000,
        type=ADJUSTMENT_ACTION_TYPE_CURRENCY,
        min_limit_error_message="Minimum daily budget must be {min_limit:.2f}{sign} or greater.",
        max_limit_error_message="Minimum daily budget must be {max_limit:.2f}{sign} or less.",
    ),
}

_VALID_LEFT_OPERAND_TYPES = set(constants.MetricType.get_all()) - constants.CONTENT_AD_SETTINGS
VALID_LEFT_OPERAND_TYPES_FOR_RULE_TARGET = {t: set(_VALID_LEFT_OPERAND_TYPES) for t in constants.TargetType.get_all()}
VALID_LEFT_OPERAND_TYPES_FOR_RULE_TARGET[constants.TargetType.AD] |= constants.CONTENT_AD_SETTINGS

VALID_RIGHT_OPERAND_TYPES = {constants.ValueType.ABSOLUTE}

PERCENT_MODIFIER_LEFT_OPERAND_TYPES = {
    constants.MetricType.CAMPAIGN_PRIMARY_GOAL,
    constants.MetricType.AD_GROUP_DAILY_CAP,
}

DAY_MODIFIER_LEFT_OPERAND_TYPES = {
    constants.MetricType.ACCOUNT_CREATED_DATE,
    constants.MetricType.CAMPAIGN_CREATED_DATE,
    constants.MetricType.AD_GROUP_CREATED_DATE,
    constants.MetricType.AD_GROUP_START_DATE,
    constants.MetricType.AD_GROUP_END_DATE,
    constants.MetricType.AD_CREATED_DATE,
    constants.MetricType.CAMPAIGN_BUDGET_START_DATE,
    constants.MetricType.CAMPAIGN_BUDGET_END_DATE,
}

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
    constants.EmailActionMacro.AVG_COST_PER_UNIQUE_USER,
}

EMAIL_ACTION_MACROS_VALID_WINDOWS = {
    constants.MetricWindow.LAST_DAY,
    constants.MetricWindow.LAST_3_DAYS,
    constants.MetricWindow.LAST_7_DAYS,
    constants.MetricWindow.LAST_30_DAYS,
    constants.MetricWindow.LAST_60_DAYS,
}

INT_OPERANDS = {
    constants.MetricType.CAMPAIGN_TYPE,
    constants.MetricType.CAMPAIGN_CATEGORY,
    constants.MetricType.CAMPAIGN_LANGUAGE,
    constants.MetricType.AD_GROUP_BIDDING_TYPE,
    constants.MetricType.AD_GROUP_DELIVERY_TYPE,
    constants.MetricType.DAYS_SINCE_ACCOUNT_CREATED,
    constants.MetricType.DAYS_SINCE_CAMPAIGN_CREATED,
    constants.MetricType.DAYS_SINCE_AD_GROUP_CREATED,
    constants.MetricType.DAYS_SINCE_AD_CREATED,
    constants.MetricType.DAYS_SINCE_CAMPAIGN_BUDGET_START,
    constants.MetricType.DAYS_UNTIL_CAMPAIGN_BUDGET_END,
}

FLOAT_OPERANDS = {
    constants.MetricType.TOTAL_SPEND,
    constants.MetricType.IMPRESSIONS,
    constants.MetricType.CLICKS,
    constants.MetricType.CTR,
    constants.MetricType.AVG_CPC,
    constants.MetricType.AVG_CPM,
    constants.MetricType.VISITS,
    constants.MetricType.NEW_VISITS,
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
    constants.MetricType.AVG_COST_PER_VISIT,
    constants.MetricType.AVG_COST_PER_NEW_VISITOR,
    constants.MetricType.AVG_COST_PER_PAGEVIEW,
    constants.MetricType.AVG_COST_PER_NON_BOUNCED_VISIT,
    constants.MetricType.AVG_COST_PER_MINUTE,
    constants.MetricType.AVG_COST_PER_UNIQUE_USER,
    constants.MetricType.AVG_COST_PER_CONVERSION,
    constants.MetricType.CONVERSIONS,
    constants.MetricType.ROAS,
    constants.MetricType.VIDEO_START,
    constants.MetricType.VIDEO_FIRST_QUARTILE,
    constants.MetricType.VIDEO_MIDPOINT,
    constants.MetricType.VIDEO_THIRD_QUARTILE,
    constants.MetricType.VIDEO_COMPLETE,
    constants.MetricType.VIDEO_START_PERCENT,
    constants.MetricType.VIDEO_FIRST_QUARTILE_PERCENT,
    constants.MetricType.VIDEO_MIDPOINT_PERCENT,
    constants.MetricType.VIDEO_THIRD_QUARTILE_PERCENT,
    constants.MetricType.VIDEO_COMPLETE,
    constants.MetricType.AVG_CPV,
    constants.MetricType.AVG_CPCV,
    constants.MetricType.AD_GROUP_BID,
    constants.MetricType.AD_GROUP_DAILY_CAP,
    constants.MetricType.MRC50_MEASURABLE,
    constants.MetricType.MRC50_VIEWABLE,
    constants.MetricType.MRC50_MEASURABLE_PERCENT,
    constants.MetricType.MRC50_VIEWABLE_PERCENT,
    constants.MetricType.MRC50_VCPM,
}

DECIMAL_OPERANDS = {constants.MetricType.CAMPAIGN_BUDGET_MARGIN, constants.MetricType.CAMPAIGN_REMAINING_BUDGET}

STRING_OPERANDS = {
    constants.MetricType.ACCOUNT_NAME,
    constants.MetricType.CAMPAIGN_NAME,
    constants.MetricType.CAMPAIGN_MANAGER,
    constants.MetricType.AD_GROUP_NAME,
    constants.MetricType.AD_TITLE,
    constants.MetricType.AD_LABEL,
}

DATE_OPERANDS = {
    constants.MetricType.ACCOUNT_CREATED_DATE,
    constants.MetricType.CAMPAIGN_CREATED_DATE,
    constants.MetricType.AD_GROUP_CREATED_DATE,
    constants.MetricType.AD_GROUP_START_DATE,
    constants.MetricType.AD_GROUP_END_DATE,
    constants.MetricType.AD_CREATED_DATE,
    constants.MetricType.CAMPAIGN_BUDGET_START_DATE,
    constants.MetricType.CAMPAIGN_BUDGET_END_DATE,
}

VALID_NUMBER_OPERATORS = [constants.Operator.GREATER_THAN, constants.Operator.LESS_THAN]
VALID_STRING_OPERATORS = [
    constants.Operator.EQUALS,
    constants.Operator.NOT_EQUALS,
    constants.Operator.CONTAINS,
    constants.Operator.NOT_CONTAINS,
    constants.Operator.STARTS_WITH,
    constants.Operator.ENDS_WITH,
]
VALID_DATE_OPERATORS = [
    constants.Operator.EQUALS,
    constants.Operator.NOT_EQUALS,
    constants.Operator.LESS_THAN,
    constants.Operator.GREATER_THAN,
]
VALID_CONSTANT_OPERATORS = [constants.Operator.EQUALS, constants.Operator.NOT_EQUALS]

VALID_OPERATORS = {
    constants.MetricType.TOTAL_SPEND: VALID_NUMBER_OPERATORS,
    constants.MetricType.IMPRESSIONS: VALID_NUMBER_OPERATORS,
    constants.MetricType.CLICKS: VALID_NUMBER_OPERATORS,
    constants.MetricType.CTR: VALID_NUMBER_OPERATORS,
    constants.MetricType.AVG_CPC: VALID_NUMBER_OPERATORS,
    constants.MetricType.AVG_CPM: VALID_NUMBER_OPERATORS,
    constants.MetricType.VISITS: VALID_NUMBER_OPERATORS,
    constants.MetricType.NEW_VISITS: VALID_NUMBER_OPERATORS,
    constants.MetricType.UNIQUE_USERS: VALID_NUMBER_OPERATORS,
    constants.MetricType.NEW_USERS: VALID_NUMBER_OPERATORS,
    constants.MetricType.RETURNING_USERS: VALID_NUMBER_OPERATORS,
    constants.MetricType.NEW_USERS_RATIO: VALID_NUMBER_OPERATORS,
    constants.MetricType.CLICK_DISCREPANCY: VALID_NUMBER_OPERATORS,
    constants.MetricType.PAGEVIEWS: VALID_NUMBER_OPERATORS,
    constants.MetricType.PAGEVIEWS_PER_VISIT: VALID_NUMBER_OPERATORS,
    constants.MetricType.BOUNCED_VISITS: VALID_NUMBER_OPERATORS,
    constants.MetricType.NON_BOUNCED_VISITS: VALID_NUMBER_OPERATORS,
    constants.MetricType.BOUNCE_RATE: VALID_NUMBER_OPERATORS,
    constants.MetricType.TOTAL_SECONDS: VALID_NUMBER_OPERATORS,
    constants.MetricType.AVG_TIME_ON_SITE: VALID_NUMBER_OPERATORS,
    constants.MetricType.AVG_COST_PER_VISIT: VALID_NUMBER_OPERATORS,
    constants.MetricType.AVG_COST_PER_NEW_VISITOR: VALID_NUMBER_OPERATORS,
    constants.MetricType.AVG_COST_PER_PAGEVIEW: VALID_NUMBER_OPERATORS,
    constants.MetricType.AVG_COST_PER_NON_BOUNCED_VISIT: VALID_NUMBER_OPERATORS,
    constants.MetricType.AVG_COST_PER_MINUTE: VALID_NUMBER_OPERATORS,
    constants.MetricType.AVG_COST_PER_UNIQUE_USER: VALID_NUMBER_OPERATORS,
    constants.MetricType.AVG_COST_PER_CONVERSION: VALID_NUMBER_OPERATORS,
    constants.MetricType.CONVERSIONS: VALID_NUMBER_OPERATORS,
    constants.MetricType.ROAS: VALID_NUMBER_OPERATORS,
    constants.MetricType.VIDEO_START: VALID_NUMBER_OPERATORS,
    constants.MetricType.VIDEO_FIRST_QUARTILE: VALID_NUMBER_OPERATORS,
    constants.MetricType.VIDEO_MIDPOINT: VALID_NUMBER_OPERATORS,
    constants.MetricType.VIDEO_THIRD_QUARTILE: VALID_NUMBER_OPERATORS,
    constants.MetricType.VIDEO_COMPLETE: VALID_NUMBER_OPERATORS,
    constants.MetricType.VIDEO_START_PERCENT: VALID_NUMBER_OPERATORS,
    constants.MetricType.VIDEO_FIRST_QUARTILE_PERCENT: VALID_NUMBER_OPERATORS,
    constants.MetricType.VIDEO_MIDPOINT_PERCENT: VALID_NUMBER_OPERATORS,
    constants.MetricType.VIDEO_THIRD_QUARTILE_PERCENT: VALID_NUMBER_OPERATORS,
    constants.MetricType.VIDEO_COMPLETE_PERCENT: VALID_NUMBER_OPERATORS,
    constants.MetricType.AVG_CPV: VALID_NUMBER_OPERATORS,
    constants.MetricType.AVG_CPCV: VALID_NUMBER_OPERATORS,
    constants.MetricType.MRC50_MEASURABLE: VALID_NUMBER_OPERATORS,
    constants.MetricType.MRC50_VIEWABLE: VALID_NUMBER_OPERATORS,
    constants.MetricType.MRC50_MEASURABLE_PERCENT: VALID_NUMBER_OPERATORS,
    constants.MetricType.MRC50_VIEWABLE_PERCENT: VALID_NUMBER_OPERATORS,
    constants.MetricType.MRC50_VCPM: VALID_NUMBER_OPERATORS,
    constants.MetricType.ACCOUNT_NAME: VALID_STRING_OPERATORS,
    constants.MetricType.ACCOUNT_CREATED_DATE: VALID_DATE_OPERATORS,
    constants.MetricType.DAYS_SINCE_ACCOUNT_CREATED: VALID_DATE_OPERATORS,
    constants.MetricType.CAMPAIGN_NAME: VALID_STRING_OPERATORS,
    constants.MetricType.CAMPAIGN_CREATED_DATE: VALID_DATE_OPERATORS,
    constants.MetricType.DAYS_SINCE_CAMPAIGN_CREATED: VALID_DATE_OPERATORS,
    constants.MetricType.CAMPAIGN_TYPE: VALID_CONSTANT_OPERATORS,
    constants.MetricType.CAMPAIGN_MANAGER: VALID_STRING_OPERATORS,
    constants.MetricType.CAMPAIGN_CATEGORY: VALID_CONSTANT_OPERATORS,
    constants.MetricType.CAMPAIGN_LANGUAGE: VALID_CONSTANT_OPERATORS,
    constants.MetricType.CAMPAIGN_PRIMARY_GOAL: VALID_NUMBER_OPERATORS,
    constants.MetricType.CAMPAIGN_PRIMARY_GOAL_VALUE: VALID_NUMBER_OPERATORS,
    constants.MetricType.AD_GROUP_NAME: VALID_STRING_OPERATORS,
    constants.MetricType.AD_GROUP_CREATED_DATE: VALID_DATE_OPERATORS,
    constants.MetricType.DAYS_SINCE_AD_GROUP_CREATED: VALID_DATE_OPERATORS,
    constants.MetricType.AD_GROUP_START_DATE: VALID_DATE_OPERATORS,
    constants.MetricType.AD_GROUP_END_DATE: VALID_DATE_OPERATORS,
    constants.MetricType.AD_GROUP_BIDDING_TYPE: VALID_CONSTANT_OPERATORS,
    constants.MetricType.AD_GROUP_BID: VALID_NUMBER_OPERATORS,
    constants.MetricType.AD_GROUP_DAILY_CAP: VALID_NUMBER_OPERATORS,
    constants.MetricType.AD_GROUP_DELIVERY_TYPE: VALID_CONSTANT_OPERATORS,
    constants.MetricType.AD_TITLE: VALID_STRING_OPERATORS,
    constants.MetricType.AD_LABEL: VALID_STRING_OPERATORS,
    constants.MetricType.AD_CREATED_DATE: VALID_DATE_OPERATORS,
    constants.MetricType.DAYS_SINCE_AD_CREATED: VALID_DATE_OPERATORS,
    constants.MetricType.CAMPAIGN_BUDGET_START_DATE: VALID_DATE_OPERATORS,
    constants.MetricType.DAYS_SINCE_CAMPAIGN_BUDGET_START: VALID_DATE_OPERATORS,
    constants.MetricType.CAMPAIGN_BUDGET_END_DATE: VALID_DATE_OPERATORS,
    constants.MetricType.DAYS_UNTIL_CAMPAIGN_BUDGET_END: VALID_DATE_OPERATORS,
    constants.MetricType.CAMPAIGN_BUDGET_MARGIN: VALID_NUMBER_OPERATORS,
    constants.MetricType.CAMPAIGN_REMAINING_BUDGET: VALID_NUMBER_OPERATORS,
}

STATS_FIELDS_DEFAULTS = {
    constants.MetricType.CLICKS: 0,
    constants.MetricType.IMPRESSIONS: 0,
    constants.MetricType.TOTAL_SPEND: 0,
    constants.MetricType.CTR: None,
    constants.MetricType.AVG_CPC: None,
    constants.MetricType.AVG_CPM: None,
    constants.MetricType.VISITS: 0,
    constants.MetricType.PAGEVIEWS: 0,
    constants.MetricType.CLICK_DISCREPANCY: None,
    constants.MetricType.NEW_VISITS: 0,
    constants.MetricType.NEW_USERS_RATIO: None,
    constants.MetricType.BOUNCE_RATE: None,
    constants.MetricType.PAGEVIEWS_PER_VISIT: 0,
    constants.MetricType.AVG_TIME_ON_SITE: None,
    constants.MetricType.RETURNING_USERS: 0,
    constants.MetricType.UNIQUE_USERS: 0,
    constants.MetricType.NEW_USERS: 0,
    constants.MetricType.BOUNCED_VISITS: 0,
    constants.MetricType.TOTAL_SECONDS: 0,
    constants.MetricType.NON_BOUNCED_VISITS: 0,
    constants.MetricType.AVG_COST_PER_VISIT: None,
    constants.MetricType.AVG_COST_PER_NEW_VISITOR: None,
    constants.MetricType.AVG_COST_PER_PAGEVIEW: None,
    constants.MetricType.AVG_COST_PER_NON_BOUNCED_VISIT: None,
    constants.MetricType.AVG_COST_PER_MINUTE: None,
    constants.MetricType.AVG_COST_PER_UNIQUE_USER: None,
    constants.MetricType.VIDEO_START: 0,
    constants.MetricType.VIDEO_FIRST_QUARTILE: 0,
    constants.MetricType.VIDEO_MIDPOINT: 0,
    constants.MetricType.VIDEO_THIRD_QUARTILE: 0,
    constants.MetricType.VIDEO_COMPLETE: 0,
    constants.MetricType.AVG_CPV: None,
    constants.MetricType.AVG_CPCV: None,
    constants.MetricType.VIDEO_START_PERCENT: None,
    constants.MetricType.VIDEO_FIRST_QUARTILE_PERCENT: None,
    constants.MetricType.VIDEO_MIDPOINT_PERCENT: None,
    constants.MetricType.VIDEO_THIRD_QUARTILE_PERCENT: None,
    constants.MetricType.VIDEO_COMPLETE_PERCENT: None,
    constants.MetricType.MRC50_MEASURABLE: 0,
    constants.MetricType.MRC50_VIEWABLE: 0,
    constants.MetricType.MRC50_MEASURABLE_PERCENT: None,
    constants.MetricType.MRC50_VIEWABLE_PERCENT: None,
    constants.MetricType.MRC50_VCPM: None,
}

CONVERSION_FIELDS_DEFAULTS = {
    constants.MetricType.CONVERSIONS: 0,
    constants.MetricType.AVG_COST_PER_CONVERSION: None,
    constants.MetricType.ROAS: None,
}
