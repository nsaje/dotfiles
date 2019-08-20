from decimal import Decimal

from dash.constants import BiddingType
from dash.constants import CampaignGoalKPI

from .constants import BidChangeComment

# Autopilot General Settings
SYNC_IS_RECENT_HOURS = 2
AUTOMATION_AI_NAME = "Zemanta Autopilot"
AUTOPILOT_EMAIL = "help@zemanta.com"
AUTOPILOT_EMAIL_FOR_COPIES = "autopilot@zemanta.com"


# CPC Autopilot Settings
AUTOPILOT_CPC_CHANGE_TABLE = (
    {"underspend_upper_limit": -1, "underspend_lower_limit": -0.8, "bid_proc_increase": Decimal("1.0")},
    {"underspend_upper_limit": -0.8, "underspend_lower_limit": -0.6, "bid_proc_increase": Decimal("0.5")},
    {"underspend_upper_limit": -0.6, "underspend_lower_limit": -0.4, "bid_proc_increase": Decimal("0.25")},
    {"underspend_upper_limit": -0.4, "underspend_lower_limit": -0.2, "bid_proc_increase": Decimal("0.1")},
    {"underspend_upper_limit": -0.2, "underspend_lower_limit": -0.1, "bid_proc_increase": Decimal("0.05")},
    {"underspend_upper_limit": -0.1, "underspend_lower_limit": -0.05, "bid_proc_increase": Decimal("0.02")},
    {"underspend_upper_limit": -0.05, "underspend_lower_limit": -0.01, "bid_proc_increase": Decimal("0.01")},
    {"underspend_upper_limit": -0.01, "underspend_lower_limit": 10000.00, "bid_proc_increase": Decimal("-0.05")},
)

AUTOPILOT_CPC_CHANGE_PERFORMANCE_FACTOR_TABLE = (
    {"performance_upper_limit": 1.0, "performance_lower_limit": 0.75, "performance_factor": Decimal("1.0")},
    {"performance_upper_limit": 0.75, "performance_lower_limit": 0.6, "performance_factor": Decimal("0.99")},
    {"performance_upper_limit": 0.6, "performance_lower_limit": 0.4, "performance_factor": Decimal("0.975")},
    {"performance_upper_limit": 0.4, "performance_lower_limit": 0.2, "performance_factor": Decimal("0.96")},
    {"performance_upper_limit": 0.2, "performance_lower_limit": 0.0, "performance_factor": Decimal("0.95")},
)

AUTOPILOT_MIN_CPC = Decimal("0.005")
AUTOPILOT_MAX_CPC = Decimal("10.0")
AUTOPILOT_MIN_REDUCING_CPC_CHANGE = Decimal("0.001")
AUTOPILOT_MAX_REDUCING_CPC_CHANGE = Decimal("0.4")
AUTOPILOT_MIN_INCREASING_CPC_CHANGE = Decimal("0.001")
AUTOPILOT_MAX_INCREASING_CPC_CHANGE = Decimal("0.5")
AUTOPILOT_MAX_ALLOWED_CPC_SPENDING = AUTOPILOT_CPC_CHANGE_TABLE[-1]["underspend_lower_limit"]
AUTOPILOT_CPC_NO_SPEND_CHANGE = Decimal("0.3")
AUTOPILOT_CPC_NO_SPEND_THRESHOLD = Decimal("0.01")


# CPM Autopilot Settings
AUTOPILOT_CPM_CHANGE_TABLE = (
    {"underspend_upper_limit": -1, "underspend_lower_limit": -0.8, "bid_proc_increase": Decimal("1.0")},
    {"underspend_upper_limit": -0.8, "underspend_lower_limit": -0.6, "bid_proc_increase": Decimal("0.5")},
    {"underspend_upper_limit": -0.6, "underspend_lower_limit": -0.4, "bid_proc_increase": Decimal("0.25")},
    {"underspend_upper_limit": -0.4, "underspend_lower_limit": -0.2, "bid_proc_increase": Decimal("0.1")},
    {"underspend_upper_limit": -0.2, "underspend_lower_limit": -0.1, "bid_proc_increase": Decimal("0.05")},
    {"underspend_upper_limit": -0.1, "underspend_lower_limit": -0.05, "bid_proc_increase": Decimal("0.02")},
    {"underspend_upper_limit": -0.05, "underspend_lower_limit": -0.01, "bid_proc_increase": Decimal("0.01")},
    {"underspend_upper_limit": -0.01, "underspend_lower_limit": 10000.00, "bid_proc_increase": Decimal("-0.05")},
)

AUTOPILOT_CPM_CHANGE_PERFORMANCE_FACTOR_TABLE = (
    {"performance_upper_limit": 1.0, "performance_lower_limit": 0.75, "performance_factor": Decimal("1.0")},
    {"performance_upper_limit": 0.75, "performance_lower_limit": 0.6, "performance_factor": Decimal("0.99")},
    {"performance_upper_limit": 0.6, "performance_lower_limit": 0.4, "performance_factor": Decimal("0.975")},
    {"performance_upper_limit": 0.4, "performance_lower_limit": 0.2, "performance_factor": Decimal("0.96")},
    {"performance_upper_limit": 0.2, "performance_lower_limit": 0.0, "performance_factor": Decimal("0.95")},
)

AUTOPILOT_MIN_CPM = Decimal("0.01")
AUTOPILOT_MAX_CPM = Decimal("25.0")
AUTOPILOT_MIN_REDUCING_CPM_CHANGE = Decimal("0.001")
AUTOPILOT_MAX_REDUCING_CPM_CHANGE = Decimal("0.5")
AUTOPILOT_MIN_INCREASING_CPM_CHANGE = Decimal("0.001")
AUTOPILOT_MAX_INCREASING_CPM_CHANGE = Decimal("0.5")
AUTOPILOT_MAX_ALLOWED_CPM_SPENDING = AUTOPILOT_CPM_CHANGE_TABLE[-1]["underspend_lower_limit"]
AUTOPILOT_CPM_NO_SPEND_CHANGE = Decimal("0.3")
AUTOPILOT_CPM_NO_SPEND_THRESHOLD = Decimal("0.01")


# CPC/CPM Autopilot Settings
AUTOPILOT_BID_MAX_DEC_PLACES = 3
BID_CHANGE_ALLOWED_COMMENTS = [
    BidChangeComment.CURRENT_BID_TOO_HIGH,
    BidChangeComment.CURRENT_BID_TOO_LOW,
    BidChangeComment.OVER_SOURCE_MAX_BID,
    BidChangeComment.UNDER_SOURCE_MIN_BID,
    BidChangeComment.OVER_AD_GROUP_MAX_BID,
    BidChangeComment.OVER_AUTOPILOT_MAX_BID,
    BidChangeComment.UNDER_AUTOPILOT_MIN_BID,
    BidChangeComment.CURRENT_BID_TOO_HIGH,
    BidChangeComment.CURRENT_BID_TOO_LOW,
    BidChangeComment.OVER_ACCOUNT_SOURCE_MIN_BID,
    BidChangeComment.UNDER_ACCOUNT_SOURCE_MIN_BID,
    BidChangeComment.OVER_AD_GROUP_SOURCE_MIN_BID,
    BidChangeComment.UNDER_AD_GROUP_SOURCE_MIN_BID,
    BidChangeComment.BID_CONSTRAINT_APPLIED,
    BidChangeComment.UNDER_GOAL_BID,
]


def get_autopilot_bid_change_table(bidding_type):
    return AUTOPILOT_CPM_CHANGE_TABLE if bidding_type == BiddingType.CPM else AUTOPILOT_CPC_CHANGE_TABLE


def get_autopilot_bid_change_performance_factor_table(bidding_type):
    return (
        AUTOPILOT_CPM_CHANGE_PERFORMANCE_FACTOR_TABLE
        if bidding_type == BiddingType.CPM
        else AUTOPILOT_CPC_CHANGE_PERFORMANCE_FACTOR_TABLE
    )


def get_autopilot_min_bid(bidding_type):
    return AUTOPILOT_MIN_CPM if bidding_type == BiddingType.CPM else AUTOPILOT_MIN_CPC


def get_autopilot_max_bid(bidding_type):
    return AUTOPILOT_MAX_CPM if bidding_type == BiddingType.CPM else AUTOPILOT_MAX_CPC


def get_autopilot_min_reducing_bid_change(bidding_type):
    return AUTOPILOT_MIN_REDUCING_CPM_CHANGE if bidding_type == BiddingType.CPM else AUTOPILOT_MIN_REDUCING_CPC_CHANGE


def get_autopilot_max_reducing_bid_change(bidding_type):
    return AUTOPILOT_MAX_REDUCING_CPM_CHANGE if bidding_type == BiddingType.CPM else AUTOPILOT_MAX_REDUCING_CPC_CHANGE


def get_autopilot_min_increasing_bid_change(bidding_type):
    return (
        AUTOPILOT_MIN_INCREASING_CPM_CHANGE if bidding_type == BiddingType.CPM else AUTOPILOT_MIN_INCREASING_CPC_CHANGE
    )


def get_autopilot_max_increasing_bid_change(bidding_type):
    return (
        AUTOPILOT_MAX_INCREASING_CPM_CHANGE if bidding_type == BiddingType.CPM else AUTOPILOT_MAX_INCREASING_CPC_CHANGE
    )


def get_autopilot_max_allowed_bid_spending(bidding_type):
    return AUTOPILOT_MAX_ALLOWED_CPM_SPENDING if bidding_type == BiddingType.CPM else AUTOPILOT_MAX_ALLOWED_CPC_SPENDING


def get_autopilot_bid_no_spend_change(bidding_type):
    return AUTOPILOT_CPM_NO_SPEND_CHANGE if bidding_type == BiddingType.CPM else AUTOPILOT_CPC_NO_SPEND_CHANGE


def get_autopilot_bid_no_spend_threshold(bidding_type):
    return AUTOPILOT_CPM_NO_SPEND_THRESHOLD if bidding_type == BiddingType.CPM else AUTOPILOT_CPC_NO_SPEND_THRESHOLD


# Budget Autopilot Settings
MAX_BUDGET_GAIN = Decimal(1.2)
MAX_BUDGET_LOSS = Decimal(0.7)
BUDGET_AP_MIN_SOURCE_BUDGET = Decimal(5.0)
GOALS_COLUMNS = {
    CampaignGoalKPI.MAX_BOUNCE_RATE: {"col": "bounce_rate", "importance": 0.7, "spend_perc": Decimal(0.3)},
    CampaignGoalKPI.TIME_ON_SITE: {"col": "avg_tos", "importance": 0.7, "spend_perc": Decimal(0.3)},
    CampaignGoalKPI.PAGES_PER_SESSION: {"col": "pv_per_visit", "importance": 0.7, "spend_perc": Decimal(0.3)},
    CampaignGoalKPI.CPA: {"col": "conversions", "importance": 0.8, "spend_perc": Decimal(0.2)},  # actions per cost
    CampaignGoalKPI.CPC: {"col": "cpc", "col_bcm_v2": "etfm_cpc", "importance": 0.7, "spend_perc": Decimal(0.3)},
    CampaignGoalKPI.NEW_UNIQUE_VISITORS: {"col": "percent_new_users", "importance": 0.7, "spend_perc": Decimal(0.3)},
    CampaignGoalKPI.CPV: {
        "col": "avg_cost_per_visit",
        "col_bcm_v2": "avg_etfm_cost_per_visit",
        "importance": 0.7,
        "spend_perc": Decimal(0.3),
    },
    CampaignGoalKPI.CP_NON_BOUNCED_VISIT: {
        "col": "avg_cost_per_non_bounced_visit",
        "col_bcm_v2": "avg_etfm_cost_per_non_bounced_visit",
        "importance": 0.7,
        "spend_perc": Decimal(0.3),
    },
    CampaignGoalKPI.CP_NEW_VISITOR: {
        "col": "avg_cost_for_new_visitor",
        "col_bcm_v2": "avg_etfm_cost_for_new_visitor",
        "importance": 0.7,
        "spend_perc": Decimal(0.3),
    },
    CampaignGoalKPI.CP_PAGE_VIEW: {
        "col": "avg_cost_per_pageview",
        "col_bcm_v2": "avg_etfm_cost_per_pageview",
        "importance": 0.7,
        "spend_perc": Decimal(0.3),
    },
    CampaignGoalKPI.CPCV: {
        "col": "video_cpcv",
        "col_bcm_v2": "video_etfm_cpcv",
        "importance": 0.7,
        "spend_perc": Decimal(0.3),
    },
}
GOALS_WORST_VALUE = {
    "bounce_rate": 100.00,
    "spend": Decimal(0.00),
    "avg_tos": 0.0,
    "pv_per_visit": 0.0,
    "cpc": None,
    "avg_cost_per_visit": None,
    "percent_new_users": 0.0,
    "conversions": 0,
    "avg_cost_per_non_bounced_visit": None,
    "avg_etfm_cost_per_non_bounced_visit": None,
    "avg_cost_for_new_visitor": None,
    "avg_etfm_cost_for_new_visitor": None,
    "avg_cost_per_pageview": None,
    "avg_etfm_cost_per_pageview": None,
    "video_cpcv": None,
    "video_etfm_cpcv": None,
}
GOALS_CALC_COLS = {
    CampaignGoalKPI.MAX_BOUNCE_RATE: {"dividend": "bounced_visits", "divisor": "visits", "high_is_good": False},
    CampaignGoalKPI.TIME_ON_SITE: {"dividend": "total_seconds", "divisor": "visits", "high_is_good": True},
    CampaignGoalKPI.PAGES_PER_SESSION: {"dividend": "pageviews", "divisor": "visits", "high_is_good": True},
    CampaignGoalKPI.CPA: {
        "dividend": "conversions",
        "divisor": "media_cost",
        "divisor_bcm_v2": "etfm_cost",
        "high_is_good": True,
    },
    CampaignGoalKPI.CPC: {
        "dividend": "media_cost",
        "dividend_bcm_v2": "etfm_cost",
        "divisor": "clicks",
        "high_is_good": False,
    },
    CampaignGoalKPI.NEW_UNIQUE_VISITORS: {"dividend": "new_users", "divisor": "visits", "high_is_good": True},
    CampaignGoalKPI.CPV: {
        "dividend": "media_cost",
        "dividend_bcm_v2": "etfm_cost",
        "divisor": "visits",
        "high_is_good": False,
    },
    CampaignGoalKPI.CP_NON_BOUNCED_VISIT: {
        "dividend": "media_cost",
        "dividend_bcm_v2": "etfm_cost",
        "divisor": "non_bounced_visits",
        "high_is_good": False,
    },
    CampaignGoalKPI.CP_NEW_VISITOR: {
        "dividend": "media_cost",
        "dividend_bcm_v2": "etfm_cost",
        "divisor": "new_users",
        "high_is_good": False,
    },
    CampaignGoalKPI.CP_PAGE_VIEW: {
        "dividend": "media_cost",
        "dividend_bcm_v2": "etfm_cost",
        "divisor": "pageviews",
        "high_is_good": False,
    },
    CampaignGoalKPI.CPCV: {
        "dividend": "media_cost",
        "dividend_bcm_v2": "etfm_cost",
        "divisor": "video_complete",
        "high_is_good": False,
    },
}
SPEND_PERC_LOWERING_THRESHOLD = 1.0
LOW_SPEND_PROB_LOWERING_FACTOR = 0.25
AUTOPILOT_DATA_LOOKBACK_DAYS = 2
AUTOPILOT_CONVERSION_DATA_LOOKBACK_DAYS = 14
AUTOPILOT_MIN_SPEND_PERC = Decimal(0.50)
BUDGET_AUTOPILOT_MIN_DAILY_BUDGET_PER_SOURCE_CALC = Decimal(10)
BID_GOAL_THRESHOLD = Decimal("0.8")
