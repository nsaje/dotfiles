from decimal import Decimal
from .constants import CpcChangeComment as cpc_com
from dash.constants import CampaignGoalKPI

# Autopilot General Settings
SYNC_IS_RECENT_HOURS = 2
AUTOMATION_AI_NAME = 'Zemanta Autopilot'
AUTOPILOT_EMAIL = 'help@zemanta.com'
AUTOPILOT_EMAIL_FOR_COPIES = 'autopilot@zemanta.com'


# CPC Autopilot Settings
AUTOPILOT_CPC_CHANGE_TABLE = (
    {'underspend_upper_limit': -1, 'underspend_lower_limit': -0.8, 'bid_cpc_proc_increase': Decimal('1.0')},
    {'underspend_upper_limit': -0.8, 'underspend_lower_limit': -0.6, 'bid_cpc_proc_increase': Decimal('0.5')},
    {'underspend_upper_limit': -0.6, 'underspend_lower_limit': -0.4, 'bid_cpc_proc_increase': Decimal('0.25')},
    {'underspend_upper_limit': -0.4, 'underspend_lower_limit': -0.2, 'bid_cpc_proc_increase': Decimal('0.1')},
    {'underspend_upper_limit': -0.2, 'underspend_lower_limit': -0.1, 'bid_cpc_proc_increase': Decimal('0.05')},
    {'underspend_upper_limit': -0.1, 'underspend_lower_limit': -0.05, 'bid_cpc_proc_increase': Decimal('-0.02')},
    {'underspend_upper_limit': -0.05, 'underspend_lower_limit': -0.01, 'bid_cpc_proc_increase': Decimal('-0.1')},
    {'underspend_upper_limit': -0.01, 'underspend_lower_limit': 100.00, 'bid_cpc_proc_increase': Decimal('-0.15')}
)

AUTOPILOT_CPC_CHANGE_PERFORMANCE_FACTOR_TABLE = (
    {'performance_upper_limit': 1.0, 'performance_lower_limit': 0.75, 'performance_factor': Decimal('1.0')},
    {'performance_upper_limit': 0.75, 'performance_lower_limit': 0.6, 'performance_factor': Decimal('0.98')},
    {'performance_upper_limit': 0.6, 'performance_lower_limit': 0.4, 'performance_factor': Decimal('0.95')},
    {'performance_upper_limit': 0.4, 'performance_lower_limit': 0.2, 'performance_factor': Decimal('0.93')},
    {'performance_upper_limit': 0.2, 'performance_lower_limit': 0.0, 'performance_factor': Decimal('0.90')},
)

AUTOPILOT_MIN_CPC = Decimal('0.03')
AUTOPILOT_MAX_CPC = Decimal('10.0')
AUTOPILOT_MIN_REDUCING_CPC_CHANGE = Decimal('0.001')
AUTOPILOT_MAX_REDUCING_CPC_CHANGE = Decimal('0.40')
AUTOPILOT_MIN_INCREASING_CPC_CHANGE = Decimal('0.001')
AUTOPILOT_MAX_INCREASING_CPC_CHANGE = Decimal('0.5')
AUTOPILOT_CPC_MAX_DEC_PLACES = 3
AUTOPILOT_MAX_ALLOWED_SPENDING = AUTOPILOT_CPC_CHANGE_TABLE[-1]['underspend_lower_limit']
AUTOPILOT_OPTIMAL_SPEND = Decimal('-0.1')
AUTOPILOT_CPC_NO_SPEND_CHANGE = Decimal('0.3')
AUTOPILOT_CPC_NO_SPEND_THRESHOLD = Decimal('0.01')
CPC_CHANGE_ALLOWED_COMMENTS = [
    cpc_com.CURRENT_CPC_TOO_HIGH, cpc_com.CURRENT_CPC_TOO_LOW, cpc_com.OVER_SOURCE_MAX_CPC,
    cpc_com.UNDER_SOURCE_MIN_CPC, cpc_com.OVER_AD_GROUP_MAX_CPC, cpc_com.OVER_AUTOPILOT_MAX_CPC,
    cpc_com.UNDER_AUTOPILOT_MIN_CPC, cpc_com.CURRENT_CPC_TOO_HIGH, cpc_com.CURRENT_CPC_TOO_LOW,
    cpc_com.OVER_ACCOUNT_SOURCE_MIN_CPC, cpc_com.UNDER_ACCOUNT_SOURCE_MIN_CPC,
    cpc_com.OVER_AD_GROUP_SOURCE_MIN_CPC, cpc_com.UNDER_AD_GROUP_SOURCE_MIN_CPC,
    cpc_com.CPC_CONSTRAINT_APPLIED
]

# Budget Autopilot Settings
MAX_BUDGET_GAIN = Decimal(1.2)
MAX_BUDGET_LOSS = Decimal(0.7)
BUDGET_AP_MIN_SOURCE_BUDGET = Decimal(5.0)
GOALS_COLUMNS = {
    CampaignGoalKPI.MAX_BOUNCE_RATE: {'col': 'bounce_rate', 'importance': 0.7, 'spend_perc': Decimal(0.3)},
    CampaignGoalKPI.TIME_ON_SITE: {'col': 'avg_tos', 'importance': 0.7, 'spend_perc': Decimal(0.3)},
    CampaignGoalKPI.PAGES_PER_SESSION: {'col': 'pv_per_visit', 'importance': 0.7, 'spend_perc': Decimal(0.3)},
    CampaignGoalKPI.CPA: {'col': 'conversions', 'importance': 0.8, 'spend_perc': Decimal(0.2)},  # actions per cost
    CampaignGoalKPI.CPC: {'col': 'cpc', 'col_bcm_v2': 'etfm_cpc', 'importance': 0.7, 'spend_perc': Decimal(0.3)},
    CampaignGoalKPI.NEW_UNIQUE_VISITORS: {'col': 'percent_new_users', 'importance': 0.7, 'spend_perc': Decimal(0.3)},
    CampaignGoalKPI.CPV: {'col': 'avg_cost_per_visit', 'col_bcm_v2': 'avg_etfm_cost_per_visit', 'importance': 0.7, 'spend_perc': Decimal(0.3)},
    CampaignGoalKPI.CP_NON_BOUNCED_VISIT: {'col': 'avg_cost_per_non_bounced_visit', 'col_bcm_v2': 'avg_etfm_cost_per_non_bounced_visit', 'importance': 0.7, 'spend_perc': Decimal(0.3)},
    CampaignGoalKPI.CP_NEW_VISITOR: {'col': 'avg_cost_for_new_visitor', 'col_bcm_v2': 'avg_etfm_cost_for_new_visitor', 'importance': 0.7, 'spend_perc': Decimal(0.3)},
    CampaignGoalKPI.CP_PAGE_VIEW: {'col': 'avg_cost_per_pageview', 'col_bcm_v2': 'avg_etfm_cost_per_pageview', 'importance': 0.7, 'spend_perc': Decimal(0.3)},
    CampaignGoalKPI.CPCV: {'col': 'video_cpcv', 'col_bcm_v2': 'video_etfm_cpcv', 'importance': 0.7, 'spend_perc': Decimal(0.3)},
}
GOALS_WORST_VALUE = {
    'bounce_rate': 100.00,
    'spend': Decimal(0.00),
    'avg_tos': 0.0,
    'pv_per_visit': 0.0,
    'cpc': None,
    'avg_cost_per_visit': None,
    'percent_new_users': 0.0,
    'conversions': 0,
    'avg_cost_per_non_bounced_visit': None,
    'avg_etfm_cost_per_non_bounced_visit': None,
    'avg_cost_for_new_visitor': None,
    'avg_etfm_cost_for_new_visitor': None,
    'avg_cost_per_pageview': None,
    'avg_etfm_cost_per_pageview': None,
    'video_cpcv': None,
    'video_etfm_cpcv': None,
}
GOALS_CALC_COLS = {
    CampaignGoalKPI.MAX_BOUNCE_RATE:      {'dividend': 'bounced_visits', 'divisor': 'visits', 'high_is_good': False},
    CampaignGoalKPI.TIME_ON_SITE:         {'dividend': 'total_seconds', 'divisor': 'visits', 'high_is_good': True},
    CampaignGoalKPI.PAGES_PER_SESSION:    {'dividend': 'pageviews', 'divisor': 'visits', 'high_is_good': True},
    CampaignGoalKPI.CPA:                  {'dividend': 'conversions', 'divisor': 'media_cost',
                                           'divisor_bcm_v2': 'etfm_cost', 'high_is_good': True},
    CampaignGoalKPI.CPC:                  {'dividend': 'media_cost', 'dividend_bcm_v2': 'etfm_cost',
                                           'divisor': 'clicks', 'high_is_good': False},
    CampaignGoalKPI.NEW_UNIQUE_VISITORS:  {'dividend': 'new_users', 'divisor': 'visits', 'high_is_good': True},
    CampaignGoalKPI.CPV:                  {'dividend': 'media_cost', 'dividend_bcm_v2': 'etfm_cost',
                                           'divisor': 'visits', 'high_is_good': False},
    CampaignGoalKPI.CP_NON_BOUNCED_VISIT: {'dividend': 'media_cost', 'dividend_bcm_v2': 'etfm_cost',
                                           'divisor': 'non_bounced_visits', 'high_is_good': False},
    CampaignGoalKPI.CP_NEW_VISITOR: {'dividend': 'media_cost', 'dividend_bcm_v2': 'etfm_cost',
                                     'divisor': 'new_users', 'high_is_good': False},
    CampaignGoalKPI.CP_PAGE_VIEW: {'dividend': 'media_cost', 'dividend_bcm_v2': 'etfm_cost',
                                   'divisor': 'pageviews', 'high_is_good': False},
    CampaignGoalKPI.CPCV: {'dividend': 'media_cost', 'dividend_bcm_v2': 'etfm_cost',
                           'divisor': 'video_complete', 'high_is_good': False},
}
SPEND_PERC_LOWERING_THRESHOLD = 1.0
LOW_SPEND_PROB_LOWERING_FACTOR = 0.25
AUTOPILOT_DATA_LOOKBACK_DAYS = 2
AUTOPILOT_CONVERSION_DATA_LOOKBACK_DAYS = 14
AUTOPILOT_MIN_SPEND_PERC = Decimal(0.50)
BUDGET_AUTOPILOT_MIN_DAILY_BUDGET_PER_SOURCE_CALC = Decimal(10)
