import decimal


DEPLETING_AVAILABLE_BUDGET_SCALAR = 1.5
DEPLETING_CAMPAIGN_BUDGET_EMAIL = 'help@zemanta.com'
AUTOPILOT_CPC_CHANGE_TABLE = [
    # [underspendingUpperLimit, underspendingLowerLimit, bidCPCProcentualIncrease]
    [-1, -0.8, 0.15],
    [-0.8, -0.4, 0.1],
    [-0.4, -0.2, 0.05],
    [-0.2, -0.1, 0],
    [-0.1, 0, -0.03]
]
AUTOPILOT_MINIMUM_CPC = decimal.Decimal('0.05')
AUTOPILOT_MAXIMUM_CPC = decimal.Decimal('4.0')
AUTOMATION_AI_NAME = 'Zemanta AI'
AUTOPILOT_EMAIL = 'help@zemanta.com'
