from utils.constant_base import ConstantBase


class CampaignStopState(ConstantBase):
    ACTIVE = 1
    STOPPED = 2

    _VALUES = {
        ACTIVE: 'Enabled',
        STOPPED: 'Stopped',
    }


class CampaignStopEvent(ConstantBase):
    BUDGET_DEPLETION_CHECK = 1
    SELECTION_CHECK = 2
    MAX_ALLOWED_END_DATE_UPDATE = 3
    BUDGET_AMOUNT_VALIDATION = 4

    _VALUES = {
        BUDGET_DEPLETION_CHECK: 'Budget depletion check',
        SELECTION_CHECK: 'Selection check',
        MAX_ALLOWED_END_DATE_UPDATE: 'Max allowed end date update',
        BUDGET_AMOUNT_VALIDATION: 'Budget amount validation',
    }
