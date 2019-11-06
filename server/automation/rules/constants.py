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
    SOURCE = 9

    _VALUES = {
        AD_GROUP: "Ad group",
        AD: "Ad",
        PUBLISHER: "Publisher",
        DEVICE: "Device",
        COUNTRY: "Country",
        STATE: "State",
        DMA: "DMA",
        OS: "Operating system",
        SOURCE: "Source",
    }


TARGET_TYPE_MV_COLUMNS_MAPPING = {
    TargetType.AD_GROUP: ["ad_group_id"],
    TargetType.AD: ["content_ad_id"],
    TargetType.PUBLISHER: ["publisher", "source_id"],
    TargetType.DEVICE: ["device_type"],
    TargetType.COUNTRY: ["country"],
    TargetType.STATE: ["state"],
    TargetType.DMA: ["dma"],
    TargetType.OS: ["device_os"],
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
    NOTIFY = 9

    _VALUES = {
        INCREASE_BID: "Increase bid",
        DECREASE_BID: "Decrease bid",
        INCREASE_BID_MODIFIER: "Increase bid modifier",
        DECREASE_BID_MODIFIER: "Decrease bid modifier",
        INCREASE_BUDGET: "Increase budget",
        DECREASE_BUDGET: "Decrease budget",
        TURN_OFF: "Turn off",
        BLACKLIST: "Blacklist",
        NOTIFY: "Send an e-mail",
    }


class NotificationType(ConstantBase):
    NONE = 1
    ON_RULE_TRIGGERED = 2
    ON_RULE_ACTION_PERFORMED = 3

    _VALUES = {
        NONE: "Never send an e-mail",
        ON_RULE_TRIGGERED: "Send an e-mail whenever the rule runs",
        ON_RULE_ACTION_PERFORMED: "Send an e-mail whenever the rule performs an action",
    }


class MetricWindow(ConstantBase):
    NOT_APPLICABLE = 1
    LAST_DAY = 2
    LAST_3_DAYS = 3
    LAST_7_DAYS = 4
    LAST_30_DAYS = 5
    LIFETIME = 6

    _VALUES = {
        NOT_APPLICABLE: "N/A",
        LAST_DAY: "Last day",
        LAST_3_DAYS: "Last 3 days",
        LAST_7_DAYS: "Last week",
        LAST_30_DAYS: "Last month",
        LIFETIME: "Lifetime",
    }


class MetricType(ConstantBase):
    DAILY_CAP = 1
    DAILY_CAP_SPENT_RATIO = 2
    BID = 3
    BID_MODIFIER = 4
    TOTAL_SPEND = 5
    PRIMARY_GOAL = 6
    IMPRESSIONS = 7
    CLICKS = 8
    CTR = 9
    AVG_CPC = 10
    AVG_CPM = 11
    VISITS = 12
    NEW_VISITS = 13
    UNIQUE_USERS = 14
    NEW_USERS = 15
    RETURNING_USERS = 16
    NEW_USERS_RATIO = 17
    CLICK_DISCREPANCY = 18
    PAGEVIEWS = 19
    PAGEVIEWS_PER_VISIT = 20
    BOUNCED_VISITS = 21
    NON_BOUNCED_VISITS = 22
    BOUNCED_RATE = 23
    TOTAL_SECONDS = 24
    AVG_TIME_ON_SITE = 25
    AVG_COST_PER_VISIT = 26
    AVG_COST_PER_NEW_VISITOR = 27
    AVG_COST_PER_PAGEVIEW = 28
    AVG_COST_PER_NON_BOUNCED_VISIT = 29
    AVG_COST_PER_MINUTE = 30
    VIDEO_START = 31
    VIDEO_FIRST_QUARTILE = 32
    VIDEO_MIDPOINT = 33
    VIDEO_THIRD_QUARTILE = 34
    VIDEO_COMPLETE = 35
    AVG_CPV = 36
    AVG_CPCV = 37

    _VALUES = {
        DAILY_CAP: "Daily cap",
        DAILY_CAP_SPENT_RATIO: "Daily cap spent percentage",
        BID: "Bid",
        BID_MODIFIER: "Bid modifier",
        TOTAL_SPEND: "Total spend",
        PRIMARY_GOAL: "Primary goal",
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
        BOUNCED_RATE: "Bounced rate",
        TOTAL_SECONDS: "Total seconds",
        AVG_TIME_ON_SITE: "Average time on site",
        AVG_COST_PER_VISIT: "Average cost per visit",
        AVG_COST_PER_NEW_VISITOR: "Average cost per new visitor",
        AVG_COST_PER_PAGEVIEW: "Average cost per pageview",
        AVG_COST_PER_NON_BOUNCED_VISIT: "Average cost per non-bounced visit",
        AVG_COST_PER_MINUTE: "Average cost per minute",
        VIDEO_START: "Video start",
        VIDEO_FIRST_QUARTILE: "Video fist quartile",
        VIDEO_MIDPOINT: "Video midpoint",
        VIDEO_THIRD_QUARTILE: "Video third quartile",
        VIDEO_COMPLETE: "Video complete",
        AVG_CPV: "Average CPV",
        AVG_CPCV: "Average CPCV",
    }


METRIC_MV_COLUMNS_MAPPING = {
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
    MetricType.BOUNCED_RATE: "bounce_rate",
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
    MetricType.VIDEO_START: "video_start",
    MetricType.VIDEO_FIRST_QUARTILE: "video_first_quartile",
    MetricType.VIDEO_MIDPOINT: "video_midpoint",
    MetricType.VIDEO_THIRD_QUARTILE: "video_third_quartile",
    MetricType.VIDEO_COMPLETE: "video_complete",
    MetricType.AVG_CPV: "local_video_etfm_cpv",
    MetricType.AVG_CPCV: "local_video_etfm_cpcv",
}


# TODO: find a better name
class ValueType(ConstantBase):
    ABSOLUTE = 1
    CONSTANT = 2
    CURRENT_TIME = 3
    ACCOUNT_MANAGER = 4
    CAMPAIGN_GOAL = 5
    CAMPAIGN_BUDGET = 6
    REMAINING_CAMPAIGN_BUDGET = 7
    AD_GROUP_BID = 8
    AD_GROUP_CLICK_DAILY_CAP = 9
    DAILY_CAP = 10
    TOTAL_SPEND = 11
    TOTAL_SPEND_DAILY_AVG = 12

    _VALUES = {
        ABSOLUTE: "Absolute value",
        CONSTANT: "Constant",
        CURRENT_TIME: "Current time",
        ACCOUNT_MANAGER: "Account manager",
        CAMPAIGN_GOAL: "Campaign goal",
        CAMPAIGN_BUDGET: "Campaign budget",
        REMAINING_CAMPAIGN_BUDGET: "Remaining campaign budget",
        AD_GROUP_BID: "Ad group bid",
        AD_GROUP_CLICK_DAILY_CAP: "Ad group click daily cap",
        DAILY_CAP: "Daily cap",
        TOTAL_SPEND: "Total spend",
        TOTAL_SPEND_DAILY_AVG: "Total spend (daily average)",  # TODO: AUTOCAMP
    }


VALUE_MV_COLUMNS_MAPPING = {ValueType.TOTAL_SPEND: "local_etfm_cost"}


class Operator(ConstantBase):
    EQUALS = 1
    NOT_EQUALS = 2
    LESS_THAN = 3
    GREATER_THAN = 4
    BETWEEN = 5  # will this just be possible user input and then 2 conditions are created automatically?
    NOT_BETWEEN = 6  # same ^
    CONTAINS = 7
    NOT_CONTAINS = 8

    _VALUES = {
        EQUALS: "Is equal to",
        NOT_EQUALS: "Is not equal to",
        LESS_THAN: "Is less than",
        GREATER_THAN: "Is greater than",
        BETWEEN: "Is between",
        NOT_BETWEEN: "Is not between",
        CONTAINS: "Contains",
        NOT_CONTAINS: "Does not contain",
    }


class ApplyStatus(ConstantBase):
    SUCCESS = 1
    FAILURE = 2

    _VALUES = {SUCCESS: "Rule application successful", FAILURE: "Rule application failed"}
