from utils.constant_base import ConstantBase


class Action(ConstantBase):
    FETCH_REPORTS = 'get_reports'
    FETCH_CAMPAIGN_STATUS = 'get_campaign_status'
    SET_CAMPAIGN_STATE = 'set_campaign_state'
    SET_PROPERTY = 'set_property'
    CREATE_CAMPAIGN = 'create_campaign'

    _VALUES = {
        FETCH_REPORTS: 'Get reports',
        FETCH_CAMPAIGN_STATUS: 'Get campaign status',
        SET_CAMPAIGN_STATE: 'Set campaign state',
        SET_PROPERTY: 'Set property',
        CREATE_CAMPAIGN: 'Create campaign',
    }


class ActionState(ConstantBase):
    FAILED = -1
    WAITING = 1
    SUCCESS = 2
    ABORTED = 3
    DELAYED = 4

    _VALUES = {
        FAILED: 'Failed',
        WAITING: 'Waiting',
        SUCCESS: 'Success',
        ABORTED: 'Aborted',
        DELAYED: 'Delayed',
    }


class ActionType(ConstantBase):
    AUTOMATIC = 1
    MANUAL = 2

    _VALUES = {
        AUTOMATIC: 'Automatic',
        MANUAL: 'Manual',
    }


class ActionLogOrderType(ConstantBase):
    FETCH_ALL = 1
    STOP_ALL = 2
    AD_GROUP_SETTINGS_UPDATE = 3
    FETCH_REPORTS = 4
    FETCH_STATUS = 5
    CREATE_CAMPAIGN = 6

    _VALUES = {
        FETCH_ALL: 'Fetch all',
        STOP_ALL: 'Stop all',
        AD_GROUP_SETTINGS_UPDATE: 'AdGroup Settings Update',
        FETCH_REPORTS: 'Fetch reports',
        FETCH_STATUS: 'Fetch status',
        CREATE_CAMPAIGN: 'Create campaign'
    }
