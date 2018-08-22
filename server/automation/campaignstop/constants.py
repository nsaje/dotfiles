from utils.constant_base import ConstantBase


class CampaignStopState(ConstantBase):
    ACTIVE = 1
    STOPPED = 2

    _VALUES = {ACTIVE: "Enabled", STOPPED: "Stopped"}


class CampaignStopEvent(ConstantBase):
    BUDGET_DEPLETION_CHECK = 1
    SELECTION_CHECK = 2
    MAX_ALLOWED_END_DATE_UPDATE = 3
    BUDGET_AMOUNT_VALIDATION = 4
    SIMPLE_CAMPAIGN_STOP = 5
    MIN_ALLOWED_START_DATE_UPDATE = 6

    _VALUES = {
        BUDGET_DEPLETION_CHECK: "Budget depletion check",
        SELECTION_CHECK: "Selection check",
        MAX_ALLOWED_END_DATE_UPDATE: "Max allowed end date update",
        MIN_ALLOWED_START_DATE_UPDATE: "Min allowed start date update",
        BUDGET_AMOUNT_VALIDATION: "Budget amount validation",
        SIMPLE_CAMPAIGN_STOP: "Simple campaign stop",
    }


class CampaignUpdateType(ConstantBase):
    BUDGET = "budget"
    DAILY_CAP = "daily_cap"
    INITIALIZATION = "initialization"
    CAMPAIGNSTOP_STATE = "campaignstopstate"

    _VALUES = {
        BUDGET: "Campaign budget update",
        DAILY_CAP: "Campaign total daily cap update",
        INITIALIZATION: "Real time campaign stop initialization",
        CAMPAIGNSTOP_STATE: "Campaign stop state changed",
    }
