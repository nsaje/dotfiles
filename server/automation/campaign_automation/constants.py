from utils.constant_base import ConstantBase


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


class AggregateType(ConstantBase):
    NOT_APPLICABLE = 1
    NONE = 2
    AVG = 3
    SUM = 4

    _VALUES = {NOT_APPLICABLE: "N/A", NONE: "No aggregation", AVG: "Average", SUM: "Sum"}


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
    ABSOLUTE = 1
    CONSTANT = 2
    DAILY_BUDGET = 3
    DAILY_BUDGET_SPENT_RATIO = 4
    BID = 5
    BID_MODIFIER = 6
    TOTAL_SPEND = 7
    PRIMARY_GOAL = 8
    IMPRESSIONS = 9
    CLICKS = 10
    CTR = 11
    AVG_CPC = 12
    AVG_CPM = 13
    VISITS = 14
    UNIQUE_USERS = 15
    NEW_USERS = 16
    RETURNING_USERS = 17
    NEW_USERS_RATIO = 18
    CLICK_DISCREPANCY = 19
    PAGEVIEWS = 20
    PAGEVIEWS_PER_VISIT = 21
    BOUNCED_VISITS = 22
    NON_BOUNCED_VISITS = 23
    BOUNCED_RATE = 24
    TOTAL_SECONDS = 25
    TIME_ON_SITE = 26
    AVG_COST_PER_VISIT = 27
    AVG_COST_PER_NEW_VISITOR = 28
    AVG_COST_PER_PAGEVIEW = 29
    AVG_COST_PER_NON_BOUNCED_VISIT = 30
    AVG_COST_PER_MINUTE = 31
    VIDEO_START = 32
    VIDEO_FIRST_QUARTILE = 33
    VIDEO_MIDPOINT = 34
    VIDEO_THIRD_QUARTILE = 35
    VIDEO_COMPLETE = 36
    AVG_CPV = 37
    AVG_CPCV = 38

    _VALUES = {
        ABSOLUTE: "Absolute value",
        CONSTANT: "Constant",
        DAILY_BUDGET: "Daily budget",  # ??
        DAILY_BUDGET_SPENT_RATIO: "Daily budget spent percentage",  # ??
        BID: "Bid",
        BID_MODIFIER: "Bid modifier",
        TOTAL_SPEND: "Total spend",
        PRIMARY_GOAL: "Primary goal",  # ??
        IMPRESSIONS: "Impressions",
        CLICKS: "Clicks",
        CTR: "CTR",
        AVG_CPC: "Average CPC",
        AVG_CPM: "Average CPM",
        VISITS: "Visits",
        UNIQUE_USERS: "Unique users",
        NEW_USERS: "New users",
        RETURNING_USERS: "Returning users",
        NEW_USERS_RATIO: "New users percentage",  # ??
        CLICK_DISCREPANCY: "Click discrepancy",
        PAGEVIEWS: "Pageviews",
        PAGEVIEWS_PER_VISIT: "Pageviews per visit",
        BOUNCED_VISITS: "Bounced visits",
        NON_BOUNCED_VISITS: "Non-bounced visits",
        BOUNCED_RATE: "Bounced rate",
        TOTAL_SECONDS: "Total seconds",
        TIME_ON_SITE: "Time on site",
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


class Operator(ConstantBase):
    EQUALS = 1
    NOT_EQUALS = 2
    LESS_THAN = 3
    GREATER_THAN = 4
    BETWEEN = 5
    NOT_BETWEEN = 6
    CONTAINS = 7
    NOT_CONTAINS = 8

    _VALUES = {
        EQUALS: "Is equal to",
        NOT_EQUALS: "Is not equal to",
        LESS_THAN: "Is less than",
        GREATER_THAN: "Is greater than",
        BETWEEN: "Is between",
        NOT_BETWEEN: "is not between",
        CONTAINS: "Contains",
        NOT_CONTAINS: "Does not contain",
    }
