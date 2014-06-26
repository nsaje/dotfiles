from utils.constant_base import ConstantBase


class Action(ConstantBase):
    FETCH_REPORTS = 'get_reports'
    FETCH_CAMPAIGN_STATUS = 'get_campaign_status'
    SET_CAMPAIGN_STATE = 'set_campaign_state'
    SET_PROPERTY = 'set_property'

    _VALUES = {
        FETCH_REPORTS: 'Get reports',
        FETCH_CAMPAIGN_STATUS: 'Get campaign status',
        SET_CAMPAIGN_STATE: 'Stop campaign',
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
        SUCCESS: 'Success',
        ABORTED: 'Aborted',
    }


class ActionType(ConstantBase):
    AUTOMATIC = 1
    MANUAL = 2

    _VALUES = {
        AUTOMATIC: 'Automatic',
        MANUAL: 'Manual',
    }
