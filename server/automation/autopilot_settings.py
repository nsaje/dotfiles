from decimal import Decimal
from constants import CpcChangeComment as cpc_com
from dash.constants import CampaignGoalKPI

# Autopilot General Settings
SYNC_IS_RECENT_HOURS = 2
AUTOMATION_AI_NAME = 'Zemanta Auto-Pilot'
AUTOPILOT_EMAIL = 'help@zemanta.com'


# CPC Autopilot Settings
AUTOPILOT_CPC_CHANGE_TABLE = (
    {'underspend_upper_limit': -1, 'underspend_lower_limit': -0.8, 'bid_cpc_proc_increase': Decimal('0.5')},
    {'underspend_upper_limit': -0.8, 'underspend_lower_limit': -0.4, 'bid_cpc_proc_increase': Decimal('0.25')},
    {'underspend_upper_limit': -0.4, 'underspend_lower_limit': -0.2, 'bid_cpc_proc_increase': Decimal('0.1')},
    {'underspend_upper_limit': -0.2, 'underspend_lower_limit': -0.1, 'bid_cpc_proc_increase': Decimal('0.05')},
    {'underspend_upper_limit': -0.1, 'underspend_lower_limit': -0.05, 'bid_cpc_proc_increase': Decimal('0')},
    {'underspend_upper_limit': -0.05, 'underspend_lower_limit': 0.2, 'bid_cpc_proc_increase': Decimal('-0.1')},
    {'underspend_upper_limit': 0.2, 'underspend_lower_limit': 100.00, 'bid_cpc_proc_increase': Decimal('-0.15')}
)
AUTOPILOT_MIN_CPC = Decimal('0.03')
AUTOPILOT_MAX_CPC = Decimal('4.0')
AUTOPILOT_MIN_REDUCING_CPC_CHANGE = Decimal('0.01')
AUTOPILOT_MAX_REDUCING_CPC_CHANGE = Decimal('0.05')
AUTOPILOT_MIN_INCREASING_CPC_CHANGE = Decimal('0.01')
AUTOPILOT_MAX_INCREASING_CPC_CHANGE = Decimal('0.5')
AUTOPILOT_MAX_ALLOWED_SPENDING = AUTOPILOT_CPC_CHANGE_TABLE[-1]['underspend_lower_limit']
AUTOPILOT_OPTIMAL_SPEND = Decimal('-0.1')
CPC_CHANGE_ALLOWED_COMMENTS = [
    cpc_com.CURRENT_CPC_TOO_HIGH, cpc_com.CURRENT_CPC_TOO_LOW, cpc_com.OVER_SOURCE_MAX_CPC,
    cpc_com.UNDER_SOURCE_MIN_CPC, cpc_com.OVER_AD_GROUP_MAX_CPC, cpc_com.OVER_AUTOPILOT_MAX_CPC,
    cpc_com.UNDER_AUTOPILOT_MIN_CPC, cpc_com.CURRENT_CPC_TOO_HIGH, cpc_com.CURRENT_CPC_TOO_LOW]

# Budget Autopilot Settings
MAX_BUDGET_GAIN = Decimal(1.2)
MAX_BUDGET_LOSS = Decimal(0.8)
BUDGET_AP_MIN_SOURCE_BUDGET = Decimal(5.0)
GOALS_COLUMNS = {
    CampaignGoalKPI.MAX_BOUNCE_RATE: {'col': ['bounce_rate', 0.7], 'spend_perc': Decimal(0.3)},
    CampaignGoalKPI.TIME_ON_SITE: {'col': ['avg_tos', 0.7], 'spend_perc': Decimal(0.3)},
    CampaignGoalKPI.PAGES_PER_SESSION: {'col': ['pv_per_visit', 0.7], 'spend_perc': Decimal(0.3)},
    CampaignGoalKPI.CPA: {'col': ['conversions', 0.4], 'spend_perc': Decimal(0.6)},
    CampaignGoalKPI.CPC: {'col': ['cpc', 0.7], 'spend_perc': Decimal(0.3)},
    CampaignGoalKPI.NEW_UNIQUE_VISITORS: {'col': ['percent_new_users', 0.7], 'spend_perc': Decimal(0.3)},
}
GOALS_WORST_VALUE = {
    'bounce_rate': 100.00,
    'spend': Decimal(0.00),
    'avg_tos': 0.0,
    'pv_per_visit': 0.0,
    'cpc': None,
    'percent_new_users': 0.0,
    'conversions': 0
}
SPEND_PERC_LOWERING_THRESHOLD = 0.8
LOW_SPEND_PROB_LOWERING_FACTOR = 0.3
AUTOPILOT_DATA_LOOKBACK_DAYS = 2
AUTOPILOT_CONVERSION_DATA_LOOKBACK_DAYS = 14
AUTOPILOT_MIN_SPEND_PERC = Decimal(0.50)
BUDGET_AUTOPILOT_MIN_DAILY_BUDGET_PER_SOURCE_CALC = Decimal(10)
