from decimal import Decimal

# Autopilot General Settings
SYNC_IS_RECENT_HOURS = 2
AUTOMATION_AI_NAME = 'Zemanta Auto-Pilot'
AUTOPILOT_EMAIL = 'help@zemanta.com'
DEBUG_EMAILS = ['davorin.kopic@zemanta.com', 'tadej.pavlic@zemanta.com', 'urska.kosec@zemanta.com']


# CPC Autopilot Settings
AUTOPILOT_CPC_CHANGE_TABLE = (
    {'underspend_upper_limit': -1, 'underspend_lower_limit': -0.8, 'bid_cpc_proc_increase': Decimal('0.5')},
    {'underspend_upper_limit': -0.8, 'underspend_lower_limit': -0.4, 'bid_cpc_proc_increase': Decimal('0.25')},
    {'underspend_upper_limit': -0.4, 'underspend_lower_limit': -0.2, 'bid_cpc_proc_increase': Decimal('0.1')},
    {'underspend_upper_limit': -0.2, 'underspend_lower_limit': -0.1, 'bid_cpc_proc_increase': Decimal('0.05')},
    {'underspend_upper_limit': -0.1, 'underspend_lower_limit': -0.05, 'bid_cpc_proc_increase': Decimal('0')},
    {'underspend_upper_limit': -0.05, 'underspend_lower_limit': 0.2, 'bid_cpc_proc_increase': Decimal('-0.1')}
)
AUTOPILOT_MIN_CPC = Decimal('0.03')
AUTOPILOT_MAX_CPC = Decimal('4.0')
AUTOPILOT_MIN_REDUCING_CPC_CHANGE = Decimal('0.01')
AUTOPILOT_MAX_REDUCING_CPC_CHANGE = Decimal('0.05')
AUTOPILOT_MIN_INCREASING_CPC_CHANGE = Decimal('0.01')
AUTOPILOT_MAX_INCREASING_CPC_CHANGE = Decimal('0.5')
AUTOPILOT_MAX_ALLOWED_SPENDING = AUTOPILOT_CPC_CHANGE_TABLE[-1]['underspend_lower_limit']
AUTOPILOT_OPTIMAL_SPEND = Decimal('-0.1')


# Budget Autopilot Settings
MAX_BUDGET_GAIN = Decimal(1.2)
MAX_BUDGET_LOSS = Decimal(0.8)
MIN_SOURCE_BUDGET = Decimal(10.0)
GOALS_COLUMNS = {
    'bounce_and_spend': {'bounce_rate': 0.7, 'spend_perc': Decimal(0.3)}
}
GOALS_WORST_VALUE = {
    'bounce_rate': 100.00,
    'spend': Decimal(0.00),
}
AUTOPILOT_DATA_LOOKBACK_DAYS = 2
AUTOPILOT_MIN_SPEND_PERC = Decimal(0.50)
BUDGET_AUTOPILOT_MIN_DAILY_BUDGET = Decimal(100)
