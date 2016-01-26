import decimal

DEPLETING_AVAILABLE_BUDGET_SCALAR = decimal.Decimal(1.5)
DEPLETING_CAMPAIGN_BUDGET_EMAIL = 'help@zemanta.com'
AUTOPILOT_CPC_CHANGE_TABLE = (
    {'underspend_upper_limit': -1, 'underspend_lower_limit': -0.8, 'bid_cpc_procentual_increase': decimal.Decimal('0.5')},
    {'underspend_upper_limit': -0.8, 'underspend_lower_limit': -0.4, 'bid_cpc_procentual_increase': decimal.Decimal('0.25')},
    {'underspend_upper_limit': -0.4, 'underspend_lower_limit': -0.2, 'bid_cpc_procentual_increase': decimal.Decimal('0.1')},
    {'underspend_upper_limit': -0.2, 'underspend_lower_limit': -0.1, 'bid_cpc_procentual_increase': decimal.Decimal('0.05')},
    {'underspend_upper_limit': -0.1, 'underspend_lower_limit': -0.05, 'bid_cpc_procentual_increase': decimal.Decimal('0')},
    {'underspend_upper_limit': -0.05, 'underspend_lower_limit': 0.2, 'bid_cpc_procentual_increase': decimal.Decimal('-0.1')}
)
AUTOPILOT_MIN_CPC = decimal.Decimal('0.03')
AUTOPILOT_MAX_CPC = decimal.Decimal('4.0')
AUTOPILOT_MIN_REDUCING_CPC_CHANGE = decimal.Decimal('0.01')
AUTOPILOT_MAX_REDUCING_CPC_CHANGE = decimal.Decimal('0.05')
AUTOPILOT_MIN_INCREASING_CPC_CHANGE = decimal.Decimal('0.01')
AUTOPILOT_MAX_INCREASING_CPC_CHANGE = decimal.Decimal('0.5')
AUTOPILOT_MAX_ALLOWED_SPENDING = AUTOPILOT_CPC_CHANGE_TABLE[-1]['underspend_lower_limit']
AUTOPILOT_OPTIMAL_SPEND = decimal.Decimal('-0.1')
SYNC_IS_RECENT_HOURS = 2
AUTOMATION_AI_NAME = 'Zemanta Auto-Pilot'
AUTOPILOT_EMAIL = 'help@zemanta.com'
