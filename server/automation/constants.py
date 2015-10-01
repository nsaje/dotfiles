from utils.constant_base import ConstantBase


class CpcChangeComment(ConstantBase):
    BUDGET_MANUALLY_CHANGED = 1
    NO_YESTERDAY_SPEND = 2
    HIGH_OVERSPEND = 3
    OLD_DATA = 4
    OPTIMAL_SPEND = 5
    BUDGET_NOT_SET = 6
    CPC_NOT_SET = 7
    CURRENT_CPC_TOO_HIGH = 8
    CURRENT_CPC_TOO_LOW = 9

    _VALUES = {
        BUDGET_MANUALLY_CHANGED: 'budget was manually changed recently',
        NO_YESTERDAY_SPEND: 'there was no spend yesterday',
        HIGH_OVERSPEND: 'media source overspent significantly considering current daily budget',
        OLD_DATA: 'latest data was not available',
        OPTIMAL_SPEND: 'it is running at optimal price for given budget',
        BUDGET_NOT_SET: 'daily budget was not set',
        CPC_NOT_SET: 'bid CPC was not set',
        CURRENT_CPC_TOO_HIGH: 'Auto-Pilot can not operate on such high CPC',
        CURRENT_CPC_TOO_LOW: 'Auto-Pilot can not operate on such low CPC'
    }
