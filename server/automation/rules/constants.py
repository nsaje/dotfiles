import core.features.bid_modifiers.constants
from utils.constant_base import ConstantBase


class RuleState(ConstantBase):

    ENABLED = 1
    PAUSED = 2

    _VALUES = {ENABLED: "Enabled", PAUSED: "Paused"}


class TargetType(ConstantBase):
    AD_GROUP = 1
    AD = 2
    PUBLISHER = 3
    DEVICE = 4
    COUNTRY = 5
    STATE = 6
    DMA = 7
    OS = 8
    ENVIRONMENT = 9
    SOURCE = 10

    _VALUES = {
        AD_GROUP: "Ad group",
        AD: "Ad",
        PUBLISHER: "Publisher",
        DEVICE: "Device",
        COUNTRY: "Country",
        STATE: "State",
        DMA: "DMA",
        OS: "Operating system",
        ENVIRONMENT: "Environment",
        SOURCE: "Source",
    }


TARGET_TYPE_STATS_MAPPING = {
    TargetType.AD_GROUP: ["ad_group_id"],
    TargetType.AD: ["content_ad_id"],
    TargetType.PUBLISHER: ["publisher", "source_id"],
    TargetType.DEVICE: ["device_type"],
    TargetType.COUNTRY: ["country"],
    TargetType.STATE: ["region"],
    TargetType.DMA: ["dma"],
    TargetType.OS: ["device_os"],
    TargetType.ENVIRONMENT: ["environment"],
    TargetType.SOURCE: ["source_id"],
}


TARGET_TYPE_BID_MODIFIER_TYPE_MAPPING = {
    TargetType.AD: core.features.bid_modifiers.constants.BidModifierType.AD,
    TargetType.PUBLISHER: core.features.bid_modifiers.constants.BidModifierType.PUBLISHER,
    TargetType.DEVICE: core.features.bid_modifiers.constants.BidModifierType.DEVICE,
    TargetType.COUNTRY: core.features.bid_modifiers.constants.BidModifierType.COUNTRY,
    TargetType.STATE: core.features.bid_modifiers.constants.BidModifierType.STATE,
    TargetType.DMA: core.features.bid_modifiers.constants.BidModifierType.DMA,
    TargetType.OS: core.features.bid_modifiers.constants.BidModifierType.OPERATING_SYSTEM,
    TargetType.ENVIRONMENT: core.features.bid_modifiers.constants.BidModifierType.ENVIRONMENT,
    TargetType.SOURCE: core.features.bid_modifiers.constants.BidModifierType.SOURCE,
}


class ActionType(ConstantBase):
    INCREASE_BID = 1
    DECREASE_BID = 2
    INCREASE_BID_MODIFIER = 3
    DECREASE_BID_MODIFIER = 4
    INCREASE_BUDGET = 5
    DECREASE_BUDGET = 6
    TURN_OFF = 7
    BLACKLIST = 8
    SEND_EMAIL = 9
    ADD_TO_PUBLISHER_GROUP = 10

    _VALUES = {
        INCREASE_BID: "Increase bid",
        DECREASE_BID: "Decrease bid",
        INCREASE_BID_MODIFIER: "Increase bid modifier",
        DECREASE_BID_MODIFIER: "Decrease bid modifier",
        INCREASE_BUDGET: "Increase budget",
        DECREASE_BUDGET: "Decrease budget",
        TURN_OFF: "Turn off",
        BLACKLIST: "Blacklist",
        SEND_EMAIL: "Send an e-mail",
        ADD_TO_PUBLISHER_GROUP: "Add to publisher group",
    }


class NotificationType(ConstantBase):
    NONE = 1
    ON_RULE_RUN = 2
    ON_RULE_ACTION_TRIGGERED = 3

    _VALUES = {
        NONE: "Never send an e-mail",
        ON_RULE_RUN: "Send an e-mail whenever the rule runs",
        ON_RULE_ACTION_TRIGGERED: "Send an e-mail whenever the rule performs an action",
    }


class MetricWindow(ConstantBase):
    LAST_DAY = 1
    LAST_3_DAYS = 2
    LAST_7_DAYS = 3
    LAST_30_DAYS = 4
    LAST_60_DAYS = 5

    _VALUES = {
        LAST_DAY: "Last day",
        LAST_3_DAYS: "Last 3 days",
        LAST_7_DAYS: "Last week",
        LAST_30_DAYS: "Last month",
        LAST_60_DAYS: "Last 60 days",
    }


class MetricType(ConstantBase):
    TOTAL_SPEND = 1
    IMPRESSIONS = 2
    CLICKS = 3
    CTR = 4
    AVG_CPC = 5
    AVG_CPM = 6
    VISITS = 7
    NEW_VISITS = 8
    UNIQUE_USERS = 9
    NEW_USERS = 10
    RETURNING_USERS = 11
    NEW_USERS_RATIO = 12
    CLICK_DISCREPANCY = 13
    PAGEVIEWS = 14
    PAGEVIEWS_PER_VISIT = 15
    BOUNCED_VISITS = 16
    NON_BOUNCED_VISITS = 17
    BOUNCE_RATE = 18
    TOTAL_SECONDS = 19
    AVG_TIME_ON_SITE = 20
    AVG_COST_PER_VISIT = 21
    AVG_COST_PER_NEW_VISITOR = 22
    AVG_COST_PER_PAGEVIEW = 23
    AVG_COST_PER_NON_BOUNCED_VISIT = 24
    AVG_COST_PER_MINUTE = 25
    AVG_COST_PER_CONVERSION = 26
    AVG_COST_PER_CONVERSION_VIEW = 27
    AVG_COST_PER_CONVERSION_TOTAL = 28
    VIDEO_START = 29
    VIDEO_FIRST_QUARTILE = 30
    VIDEO_MIDPOINT = 31
    VIDEO_THIRD_QUARTILE = 32
    VIDEO_COMPLETE = 33
    AVG_CPV = 34
    AVG_CPCV = 35
    ACCOUNT_NAME = 36
    ACCOUNT_CREATED_DATE = 37
    DAYS_SINCE_ACCOUNT_CREATED = 38
    CAMPAIGN_NAME = 39
    CAMPAIGN_CREATED_DATE = 40
    DAYS_SINCE_CAMPAIGN_CREATED = 41
    CAMPAIGN_TYPE = 42
    CAMPAIGN_MANAGER = 43
    CAMPAIGN_CATEGORY = 44
    CAMPAIGN_LANGUAGE = 45
    CAMPAIGN_PRIMARY_GOAL = 46
    CAMPAIGN_PRIMARY_GOAL_VALUE = 47
    AD_GROUP_NAME = 48
    AD_GROUP_CREATED_DATE = 49
    DAYS_SINCE_AD_GROUP_CREATED = 50
    AD_GROUP_START_DATE = 51
    AD_GROUP_END_DATE = 52
    AD_GROUP_BIDDING_TYPE = 53
    AD_GROUP_BID = 54
    AD_GROUP_DAILY_CAP = 55
    AD_GROUP_DELIVERY_TYPE = 56
    AD_TITLE = 57
    AD_LABEL = 58
    AD_CREATED_DATE = 59
    DAYS_SINCE_AD_CREATED = 60
    CAMPAIGN_BUDGET_START_DATE = 61
    DAYS_SINCE_CAMPAIGN_BUDGET_START = 62
    CAMPAIGN_BUDGET_END_DATE = 63
    DAYS_UNTIL_CAMPAIGN_BUDGET_END = 64
    CAMPAIGN_BUDGET_MARGIN = 65
    CAMPAIGN_REMAINING_BUDGET = 66
    CONVERSIONS = 67
    CONVERSIONS_VIEW = 68
    CONVERSIONS_TOTAL = 69

    _VALUES = {
        TOTAL_SPEND: "Total spend",
        IMPRESSIONS: "Impressions",
        CLICKS: "Clicks",
        CTR: "CTR",
        AVG_CPC: "Average CPC",
        AVG_CPM: "Average CPM",
        VISITS: "Visits",
        NEW_VISITS: "New visits",
        UNIQUE_USERS: "Unique users",
        NEW_USERS: "New users",
        RETURNING_USERS: "Returning users",
        NEW_USERS_RATIO: "New users percentage",
        CLICK_DISCREPANCY: "Click discrepancy",
        PAGEVIEWS: "Pageviews",
        PAGEVIEWS_PER_VISIT: "Pageviews per visit",
        BOUNCED_VISITS: "Bounced visits",
        NON_BOUNCED_VISITS: "Non-bounced visits",
        BOUNCE_RATE: "Bounce rate",
        TOTAL_SECONDS: "Total seconds",
        AVG_TIME_ON_SITE: "Average time on site",
        AVG_COST_PER_VISIT: "Average cost per visit",
        AVG_COST_PER_NEW_VISITOR: "Average cost per new visitor",
        AVG_COST_PER_PAGEVIEW: "Average cost per pageview",
        AVG_COST_PER_NON_BOUNCED_VISIT: "Average cost per non-bounced visit",
        AVG_COST_PER_MINUTE: "Average cost per minute",
        AVG_COST_PER_CONVERSION: "Average cost per conversion",
        AVG_COST_PER_CONVERSION_VIEW: "Average cost per conversion (view)",
        AVG_COST_PER_CONVERSION_TOTAL: "Average cost per conversion (total)",
        VIDEO_START: "Video start",
        VIDEO_FIRST_QUARTILE: "Video fist quartile",
        VIDEO_MIDPOINT: "Video midpoint",
        VIDEO_THIRD_QUARTILE: "Video third quartile",
        VIDEO_COMPLETE: "Video complete",
        AVG_CPV: "Average CPV",
        AVG_CPCV: "Average CPCV",
        ACCOUNT_NAME: "Account name",
        ACCOUNT_CREATED_DATE: "Account created date",
        DAYS_SINCE_ACCOUNT_CREATED: "Days since account created",
        CAMPAIGN_NAME: "Campaign name",
        CAMPAIGN_CREATED_DATE: "Campaign created date",
        DAYS_SINCE_CAMPAIGN_CREATED: "Days since campaign created",
        CAMPAIGN_TYPE: "Campaign type",
        CAMPAIGN_MANAGER: "Campaign manager",
        CAMPAIGN_CATEGORY: "Campaign category",
        CAMPAIGN_LANGUAGE: "Campaign language",
        CAMPAIGN_PRIMARY_GOAL: "Primary campaign goal",
        CAMPAIGN_PRIMARY_GOAL_VALUE: "Primary campaign goal value",
        AD_GROUP_NAME: "Ad group name",
        AD_GROUP_CREATED_DATE: "Ad group created date",
        DAYS_SINCE_AD_GROUP_CREATED: "Days since ad group created",
        AD_GROUP_START_DATE: "Ad group start date",
        AD_GROUP_END_DATE: "Ad group end date",
        AD_GROUP_BIDDING_TYPE: "Ad group bidding type",
        AD_GROUP_BID: "Ad group bid",
        AD_GROUP_DAILY_CAP: "Ad group daily cap",
        AD_GROUP_DELIVERY_TYPE: "Ad group delivery type",
        AD_TITLE: "Ad title",
        AD_LABEL: "Ad label",
        AD_CREATED_DATE: "Ad created date",
        DAYS_SINCE_AD_CREATED: "Days since ad created",
        CAMPAIGN_BUDGET_START_DATE: "Budget start date",
        DAYS_SINCE_CAMPAIGN_BUDGET_START: "Days since budget start",
        CAMPAIGN_BUDGET_END_DATE: "Budget end date",
        DAYS_UNTIL_CAMPAIGN_BUDGET_END: "Days until budget end",
        CAMPAIGN_BUDGET_MARGIN: "Budget margin",
        CAMPAIGN_REMAINING_BUDGET: "Remaining budget",
        CONVERSIONS: "Conversions (click)",
        CONVERSIONS_VIEW: "Conversions (view)",
        CONVERSIONS_TOTAL: "Conversions (total)",
    }


METRIC_STATS_MAPPING = {
    MetricType.CLICKS: "clicks",
    MetricType.IMPRESSIONS: "impressions",
    MetricType.TOTAL_SPEND: "local_etfm_cost",
    MetricType.CTR: "ctr",
    MetricType.AVG_CPC: "local_etfm_cpc",
    MetricType.AVG_CPM: "local_etfm_cpm",
    MetricType.VISITS: "visits",
    MetricType.PAGEVIEWS: "pageviews",
    MetricType.CLICK_DISCREPANCY: "click_discrepancy",
    MetricType.NEW_VISITS: "new_visits",
    MetricType.NEW_USERS_RATIO: "percent_new_users",
    MetricType.BOUNCE_RATE: "bounce_rate",
    MetricType.PAGEVIEWS_PER_VISIT: "pv_per_visit",
    MetricType.AVG_TIME_ON_SITE: "avg_tos",
    MetricType.RETURNING_USERS: "returning_users",
    MetricType.UNIQUE_USERS: "unique_users",
    MetricType.NEW_USERS: "new_users",
    MetricType.BOUNCED_VISITS: "bounced_visits",
    MetricType.TOTAL_SECONDS: "total_seconds",
    MetricType.NON_BOUNCED_VISITS: "non_bounced_visits",
    MetricType.AVG_COST_PER_VISIT: "local_avg_etfm_cost_per_visit",
    MetricType.AVG_COST_PER_NEW_VISITOR: "local_avg_etfm_cost_for_new_visitor",
    MetricType.AVG_COST_PER_PAGEVIEW: "local_avg_etfm_cost_per_pageview",
    MetricType.AVG_COST_PER_NON_BOUNCED_VISIT: "local_avg_etfm_cost_per_non_bounced_visit",
    MetricType.AVG_COST_PER_MINUTE: "local_avg_etfm_cost_per_minute",
    MetricType.AVG_COST_PER_CONVERSION: "local_avg_etfm_cost_per_conversion",
    MetricType.AVG_COST_PER_CONVERSION_VIEW: "local_avg_etfm_cost_per_conversion_view",
    MetricType.AVG_COST_PER_CONVERSION_TOTAL: "local_avg_etfm_cost_per_conversion_total",
    MetricType.VIDEO_START: "video_start",
    MetricType.VIDEO_FIRST_QUARTILE: "video_first_quartile",
    MetricType.VIDEO_MIDPOINT: "video_midpoint",
    MetricType.VIDEO_THIRD_QUARTILE: "video_third_quartile",
    MetricType.VIDEO_COMPLETE: "video_complete",
    MetricType.AVG_CPV: "local_video_etfm_cpv",
    MetricType.AVG_CPCV: "local_video_etfm_cpcv",
    MetricType.CONVERSIONS: "conversions_click",
    MetricType.CONVERSIONS_VIEW: "conversions_view",
    MetricType.CONVERSIONS_TOTAL: "conversions_total",
}


METRIC_SETTINGS_MAPPING = {
    MetricType.ACCOUNT_NAME: "account_name",
    MetricType.ACCOUNT_CREATED_DATE: "account_created_date",
    MetricType.DAYS_SINCE_ACCOUNT_CREATED: "days_since_account_created",
    MetricType.CAMPAIGN_NAME: "campaign_name",
    MetricType.CAMPAIGN_CREATED_DATE: "campaign_created_date",
    MetricType.DAYS_SINCE_CAMPAIGN_CREATED: "days_since_campaign_created",
    MetricType.CAMPAIGN_TYPE: "campaign_type",
    MetricType.CAMPAIGN_MANAGER: "campaign_manager",
    MetricType.CAMPAIGN_CATEGORY: "campaign_category",
    MetricType.CAMPAIGN_LANGUAGE: "campaign_language",
    MetricType.CAMPAIGN_PRIMARY_GOAL: "campaign_primary_goal",
    MetricType.CAMPAIGN_PRIMARY_GOAL_VALUE: "campaign_primary_goal_value",
    MetricType.AD_GROUP_NAME: "ad_group_name",
    MetricType.AD_GROUP_CREATED_DATE: "ad_group_created_date",
    MetricType.DAYS_SINCE_AD_GROUP_CREATED: "days_since_ad_group_created",
    MetricType.AD_GROUP_START_DATE: "ad_group_start_date",
    MetricType.AD_GROUP_END_DATE: "ad_group_end_date",
    MetricType.AD_GROUP_BIDDING_TYPE: "ad_group_bidding_type",
    MetricType.AD_GROUP_BID: "ad_group_bid",
    MetricType.AD_GROUP_DAILY_CAP: "ad_group_daily_cap",
    MetricType.AD_GROUP_DELIVERY_TYPE: "ad_group_delivery_type",
    MetricType.AD_TITLE: "ad_title",
    MetricType.AD_LABEL: "ad_label",
    MetricType.AD_CREATED_DATE: "ad_created_date",
    MetricType.DAYS_SINCE_AD_CREATED: "days_since_ad_created",
    MetricType.CAMPAIGN_BUDGET_START_DATE: "campaign_budget_start_date",
    MetricType.DAYS_SINCE_CAMPAIGN_BUDGET_START: "days_since_campaign_budget_start",
    MetricType.CAMPAIGN_BUDGET_END_DATE: "campaign_budget_end_date",
    MetricType.DAYS_UNTIL_CAMPAIGN_BUDGET_END: "days_until_campaign_budget_end_date",
    MetricType.CAMPAIGN_BUDGET_MARGIN: "campaign_budget_margin",
    MetricType.CAMPAIGN_REMAINING_BUDGET: "campaign_remaining_budget",
}


CONTENT_AD_SETTINGS = {
    MetricType.AD_TITLE,
    MetricType.AD_LABEL,
    MetricType.AD_CREATED_DATE,
    MetricType.DAYS_SINCE_AD_CREATED,
}

CONVERSION_METRICS = {
    MetricType.CONVERSIONS,
    MetricType.CONVERSIONS_VIEW,
    MetricType.CONVERSIONS_TOTAL,
    MetricType.AVG_COST_PER_CONVERSION,
    MetricType.AVG_COST_PER_CONVERSION_VIEW,
    MetricType.AVG_COST_PER_CONVERSION_TOTAL,
}


# TODO: find a better name
class ValueType(ConstantBase):
    ABSOLUTE = 1
    CONSTANT = 2
    CURRENT_DATE = 3
    ACCOUNT_MANAGER = 4
    CAMPAIGN_PRIMARY_GOAL_VALUE = 5
    CAMPAIGN_BUDGET = 6
    REMAINING_CAMPAIGN_BUDGET = 7
    AD_GROUP_BID = 8
    AD_GROUP_CLICK_DAILY_CAP = 9
    AD_GROUP_DAILY_CAP = 10
    AD_GROUP_DAILY_CAP_SPENT_RATIO = 11
    TOTAL_SPEND = 12
    TOTAL_SPEND_DAILY_AVG = 13

    _VALUES = {
        ABSOLUTE: "Absolute value",
        CONSTANT: "Constant",
        CURRENT_DATE: "Current date",
        ACCOUNT_MANAGER: "Account manager",
        CAMPAIGN_PRIMARY_GOAL_VALUE: "Primary campaign goal value",
        CAMPAIGN_BUDGET: "Campaign budget",
        REMAINING_CAMPAIGN_BUDGET: "Remaining campaign budget",
        AD_GROUP_BID: "Ad group bid",
        AD_GROUP_CLICK_DAILY_CAP: "Ad group click daily cap",
        AD_GROUP_DAILY_CAP: "Daily cap",
        AD_GROUP_DAILY_CAP_SPENT_RATIO: "Daily cap spent ratio",
        TOTAL_SPEND: "Total spend",
        TOTAL_SPEND_DAILY_AVG: "Total spend (daily average)",  # TODO: AUTOCAMP
    }


VALUE_STATS_MAPPING = {ValueType.TOTAL_SPEND: "local_etfm_cost"}


class Operator(ConstantBase):
    EQUALS = 1
    NOT_EQUALS = 2
    LESS_THAN = 3
    GREATER_THAN = 4
    CONTAINS = 5
    NOT_CONTAINS = 6

    _VALUES = {
        EQUALS: "Is equal to",
        NOT_EQUALS: "Is not equal to",
        LESS_THAN: "Is less than",
        GREATER_THAN: "Is greater than",
        CONTAINS: "Contains",
        NOT_CONTAINS: "Does not contain",
    }


class ApplyStatus(ConstantBase):
    SUCCESS = 1
    FAILURE = 2

    _VALUES = {SUCCESS: "Rule application successful", FAILURE: "Rule application failed"}


class EmailActionMacro(ConstantBase):
    AGENCY_ID = "AGENCY_ID"
    AGENCY_NAME = "AGENCY_NAME"
    ACCOUNT_ID = "ACCOUNT_ID"
    ACCOUNT_NAME = "ACCOUNT_NAME"
    CAMPAIGN_ID = "CAMPAIGN_ID"
    CAMPAIGN_NAME = "CAMPAIGN_NAME"
    AD_GROUP_ID = "AD_GROUP_ID"
    AD_GROUP_NAME = "AD_GROUP_NAME"
    AD_GROUP_DAILY_CAP = "AD_GROUP_DAILY_CAP"  # FIXME: name discrepancy with metrics
    CAMPAIGN_BUDGET = "CAMPAIGN_BUDGET"
    TOTAL_SPEND = "TOTAL_SPEND"
    CLICKS = "CLICKS"
    IMPRESSIONS = "IMPRESSIONS"
    AVG_CPC = "AVG_CPC"
    AVG_CPM = "AVG_CPM"
    VISITS = "VISITS"
    UNIQUE_USERS = "UNIQUE_USERS"
    NEW_USERS = "NEW_USERS"
    RETURNING_USERS = "RETURNING_USERS"
    PERCENT_NEW_USERS = "PERCENT_NEW_USERS"  # FIXME: name discrepancy with metrics
    CLICK_DISCREPANCY = "CLICK_DISCREPANCY"
    PAGEVIEWS = "PAGEVIEWS"
    PAGEVIEWS_PER_VISIT = "PAGEVIEWS_PER_VISIT"
    BOUNCED_VISITS = "BOUNCED_VISITS"
    NON_BOUNCED_VISITS = "NON_BOUNCED_VISITS"
    BOUNCE_RATE = "BOUNCE_RATE"
    TOTAL_SECONDS = "TOTAL_SECONDS"
    CONVERSIONS = "CONVERSIONS"
    CONVERSIONS_VIEW = "CONVERSIONS_VIEW"
    CONVERSIONS_TOTAL = "CONVERSIONS_TOTAL"
    AVG_TIME_ON_SITE = "AVG_TIME_ON_SITE"
    AVG_COST_PER_VISIT = "AVG_COST_PER_VISIT"
    AVG_COST_PER_NEW_VISITOR = "AVG_COST_PER_NEW_VISITOR"
    AVG_COST_PER_PAGEVIEW = "AVG_COST_PER_PAGEVIEW"
    AVG_COST_PER_NON_BOUNCED_VISIT = "AVG_COST_PER_NON_BOUNCED_VISIT"
    AVG_COST_PER_MINUTE = "AVG_COST_PER_MINUTE"
    AVG_COST_PER_CONVERSION = "AVG_COST_PER_CONVERSION"
    AVG_COST_PER_CONVERSION_VIEW = "AVG_COST_PER_CONVERSION_VIEW"
    AVG_COST_PER_CONVERSION_TOTAL = "AVG_COST_PER_CONVERSION_TOTAL"

    _VALUES = {
        AGENCY_ID: "Agency ID",
        AGENCY_NAME: "Agency name",
        ACCOUNT_ID: "Account ID",
        ACCOUNT_NAME: "Account name",
        CAMPAIGN_ID: "Campaign ID",
        CAMPAIGN_NAME: "Campaign name",
        AD_GROUP_ID: "Ad group ID",
        AD_GROUP_NAME: "Ad group name",
        AD_GROUP_DAILY_CAP: "Ad group daily cap",
        CAMPAIGN_BUDGET: "Campaign budget",
        TOTAL_SPEND: "Total spend",
        CLICKS: "Clicks",
        IMPRESSIONS: "Impressions",
        AVG_CPC: "Average CPC",
        AVG_CPM: "Average CPM",
        VISITS: "Visits",
        UNIQUE_USERS: "Unique users",
        NEW_USERS: "New users",
        RETURNING_USERS: "Returning users",
        PERCENT_NEW_USERS: "% new users",
        CLICK_DISCREPANCY: "Click discrepancy",
        PAGEVIEWS: "Pageviews",
        PAGEVIEWS_PER_VISIT: "Pageviews per visit",
        BOUNCED_VISITS: "Bounced visits",
        NON_BOUNCED_VISITS: "Non-bounced visits",
        BOUNCE_RATE: "Bounce rate",
        TOTAL_SECONDS: "Total seconds",
        CONVERSIONS: "Conversions",
        CONVERSIONS_VIEW: "Conversions (view)",
        CONVERSIONS_TOTAL: "Conversions (total)",
        AVG_TIME_ON_SITE: "Average time on site",
        AVG_COST_PER_VISIT: "Average cost per visit",
        AVG_COST_PER_NEW_VISITOR: "Average cost per new visitor",
        AVG_COST_PER_PAGEVIEW: "Average cost per pageview",
        AVG_COST_PER_NON_BOUNCED_VISIT: "Average cost per non-bounced visit",
        AVG_COST_PER_MINUTE: "Average cost per minute",
        AVG_COST_PER_CONVERSION: "Average cost per conversion",
        AVG_COST_PER_CONVERSION_VIEW: "Average cost per conversion (view)",
        AVG_COST_PER_CONVERSION_TOTAL: "Average cost per conversion (total)",
    }


EMAIL_MACRO_STATS_MAPPING = {
    EmailActionMacro.TOTAL_SPEND: "local_etfm_cost",
    EmailActionMacro.CLICKS: "clicks",
    EmailActionMacro.IMPRESSIONS: "impressions",
    EmailActionMacro.AVG_CPC: "local_etfm_cpc",
    EmailActionMacro.AVG_CPM: "local_etfm_cpm",
    EmailActionMacro.VISITS: "visits",
    EmailActionMacro.UNIQUE_USERS: "unique_users",
    EmailActionMacro.NEW_USERS: "new_users",
    EmailActionMacro.RETURNING_USERS: "returning_users",
    EmailActionMacro.PERCENT_NEW_USERS: "percent_new_users",
    EmailActionMacro.CLICK_DISCREPANCY: "click_discrepancy",
    EmailActionMacro.PAGEVIEWS: "pageviews",
    EmailActionMacro.PAGEVIEWS_PER_VISIT: "pv_per_visit",
    EmailActionMacro.BOUNCED_VISITS: "bounced_visits",
    EmailActionMacro.NON_BOUNCED_VISITS: "non_bounced_visits",
    EmailActionMacro.BOUNCE_RATE: "bounce_rate",
    EmailActionMacro.TOTAL_SECONDS: "total_seconds",
    EmailActionMacro.CONVERSIONS: "conversions_click",
    EmailActionMacro.CONVERSIONS_VIEW: "conversions_view",
    EmailActionMacro.CONVERSIONS_TOTAL: "conversions_total",
    EmailActionMacro.AVG_TIME_ON_SITE: "avg_tos",
    EmailActionMacro.AVG_COST_PER_VISIT: "local_avg_etfm_cost_per_visit",
    EmailActionMacro.AVG_COST_PER_NEW_VISITOR: "local_avg_etfm_cost_for_new_visitor",
    EmailActionMacro.AVG_COST_PER_PAGEVIEW: "local_avg_etfm_cost_per_pageview",
    EmailActionMacro.AVG_COST_PER_NON_BOUNCED_VISIT: "local_avg_etfm_cost_per_non_bounced_visit",
    EmailActionMacro.AVG_COST_PER_MINUTE: "local_avg_etfm_cost_per_minute",
    EmailActionMacro.AVG_COST_PER_CONVERSION: "local_avg_etfm_cost_per_conversion",
    EmailActionMacro.AVG_COST_PER_CONVERSION_VIEW: "local_avg_etfm_cost_per_conversion_view",
    EmailActionMacro.AVG_COST_PER_CONVERSION_TOTAL: "local_avg_etfm_cost_per_conversion_total",
}
