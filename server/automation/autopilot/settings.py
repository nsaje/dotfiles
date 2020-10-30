from decimal import Decimal

from dash.constants import BiddingType
from dash.constants import CampaignGoalKPI

# Autopilot General Settings
SYNC_IS_RECENT_HOURS = 2
AUTOMATION_AI_NAME = "Zemanta Autopilot"
AUTOPILOT_EMAIL = "help@zemanta.com"
AUTOPILOT_EMAIL_FOR_COPIES = "autopilot@zemanta.com"

# Budget Autopilot Settings
MAX_BUDGET_LOSS = Decimal(0.7)
BUDGET_AP_MIN_BUDGET = Decimal(5.0)
GOALS_COLUMNS = {
    CampaignGoalKPI.MAX_BOUNCE_RATE: {"col": "bounce_rate", "importance": 0.7, "spend_perc": Decimal(0.3)},
    CampaignGoalKPI.TIME_ON_SITE: {"col": "avg_tos", "importance": 0.7, "spend_perc": Decimal(0.3)},
    CampaignGoalKPI.PAGES_PER_SESSION: {"col": "pv_per_visit", "importance": 0.7, "spend_perc": Decimal(0.3)},
    CampaignGoalKPI.CPA: {"col": "conversions", "importance": 0.8, "spend_perc": Decimal(0.2)},  # actions per cost
    CampaignGoalKPI.CPC: {"col": "etfm_cpc", "importance": 0.7, "spend_perc": Decimal(0.3)},
    CampaignGoalKPI.NEW_UNIQUE_VISITORS: {"col": "percent_new_users", "importance": 0.7, "spend_perc": Decimal(0.3)},
    CampaignGoalKPI.CPV: {"col": "avg_etfm_cost_per_visit", "importance": 0.7, "spend_perc": Decimal(0.3)},
    CampaignGoalKPI.CP_NON_BOUNCED_VISIT: {
        "col": "avg_etfm_cost_per_non_bounced_visit",
        "importance": 0.7,
        "spend_perc": Decimal(0.3),
    },
    CampaignGoalKPI.CP_NEW_VISITOR: {
        "col": "avg_etfm_cost_per_new_visitor",
        "importance": 0.7,
        "spend_perc": Decimal(0.3),
    },
    CampaignGoalKPI.CP_PAGE_VIEW: {"col": "avg_etfm_cost_per_pageview", "importance": 0.7, "spend_perc": Decimal(0.3)},
    CampaignGoalKPI.CPCV: {"col": "video_etfm_cpcv", "importance": 0.7, "spend_perc": Decimal(0.3)},
}
GOALS_WORST_VALUE = {
    "bounce_rate": 100.00,
    "spend": Decimal(0.00),
    "avg_tos": 0.0,
    "pv_per_visit": 0.0,
    "etfm_cpc": None,
    "avg_etfm_cost_per_visit": None,
    "percent_new_users": 0.0,
    "conversions": 0,
    "avg_etfm_cost_per_non_bounced_visit": None,
    "avg_etfm_cost_per_new_visitor": None,
    "avg_etfm_cost_per_pageview": None,
    "video_etfm_cpcv": None,
}
GOALS_CALC_COLS = {
    CampaignGoalKPI.MAX_BOUNCE_RATE: {"dividend": "bounced_visits", "divisor": "visits", "high_is_good": False},
    CampaignGoalKPI.TIME_ON_SITE: {"dividend": "total_seconds", "divisor": "visits", "high_is_good": True},
    CampaignGoalKPI.PAGES_PER_SESSION: {"dividend": "pageviews", "divisor": "visits", "high_is_good": True},
    CampaignGoalKPI.CPA: {"dividend": "conversions", "divisor": "etfm_cost", "high_is_good": True},
    CampaignGoalKPI.CPC: {"dividend": "etfm_cost", "divisor": "clicks", "high_is_good": False},
    CampaignGoalKPI.NEW_UNIQUE_VISITORS: {"dividend": "new_users", "divisor": "visits", "high_is_good": True},
    CampaignGoalKPI.CPV: {"dividend": "etfm_cost", "divisor": "visits", "high_is_good": False},
    CampaignGoalKPI.CP_NON_BOUNCED_VISIT: {
        "dividend": "etfm_cost",
        "divisor": "non_bounced_visits",
        "high_is_good": False,
    },
    CampaignGoalKPI.CP_NEW_VISITOR: {"dividend": "etfm_cost", "divisor": "new_users", "high_is_good": False},
    CampaignGoalKPI.CP_PAGE_VIEW: {"dividend": "etfm_cost", "divisor": "pageviews", "high_is_good": False},
    CampaignGoalKPI.CPCV: {"dividend": "etfm_cost", "divisor": "video_complete", "high_is_good": False},
}
SPEND_PERC_LOWERING_THRESHOLD = 1.0
LOW_SPEND_PROB_LOWERING_FACTOR = 0.25
AUTOPILOT_DATA_LOOKBACK_DAYS = 2
AUTOPILOT_CONVERSION_DATA_LOOKBACK_DAYS = 14
AUTOPILOT_MIN_SPEND_PERC = Decimal(0.50)
BID_GOAL_THRESHOLD = Decimal("0.8")
