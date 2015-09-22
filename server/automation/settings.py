import decimal

DEPLETING_AVAILABLE_BUDGET_SCALAR = 1.5
DEPLETING_CAMPAIGN_BUDGET_EMAIL = 'help@zemanta.com'
AUTOPILOT_CPC_CHANGE_TABLE = (
    {'underspend_upper_limit': -1, 'underspend_lower_limit': -0.8, 'bid_cpc_procentual_increase': 0.15},
    {'underspend_upper_limit': -0.8, 'underspend_lower_limit': -0.4, 'bid_cpc_procentual_increase': 0.1},
    {'underspend_upper_limit': -0.4, 'underspend_lower_limit': -0.2, 'bid_cpc_procentual_increase': 0.05},
    {'underspend_upper_limit': -0.2, 'underspend_lower_limit': -0.1, 'bid_cpc_procentual_increase': 0},
    {'underspend_upper_limit': -0.1, 'underspend_lower_limit': 0, 'bid_cpc_procentual_increase': -0.1}
)
AUTOPILOT_MIN_CPC = decimal.Decimal('0.03')
AUTOPILOT_MAX_CPC = decimal.Decimal('4.0')
AUTOPILOT_MIN_LOWERING_CPC_CHANGE = decimal.Decimal('0.01')
AUTOPILOT_MAX_LOWERING_CPC_CHANGE = decimal.Decimal('0.05')
AUTOMATION_AI_NAME = 'Zemanta Auto-Pilot'
AUTOPILOT_EMAIL = 'help@zemanta.com'
