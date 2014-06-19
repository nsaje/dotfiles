from utils.constant_base import ConstantBase


class Action(ConstantBase):
    FETCH_REPORTS = 'get_reports'
    FETCH_CAMPAIGN_STATUS = 'get_campaign_status'
    STOP_CAMPAIGN = 'stop_campaign'
    SET_PROPERTY = 'set_property'

    _VALUES = {
        FETCH_REPORTS: 'Get reports',
        FETCH_CAMPAIGN_STATUS: 'Get campaign status',
        STOP_CAMPAIGN: 'Stop campaign',
        SET_PROPERTY: 'Set property',
    }


class ActionStatus(ConstantBase):
    FAILED = -1
    WAITING = 1
    SUCCESS = 2
    ABORTED = 3

    _VALUES = {
        FAILED: 'Failed',
        WAITING: 'Waiting',
        SUCCESS: 'Executed',
        ABORTED: 'Aborted',
    }


class ActionType(ConstantBase):
    AUTOMATIC = 1
    MANUAL = 2

    _VALUES = {
        AUTOMATIC: 'Automatic',
        MANUAL: 'Manual',
    }
