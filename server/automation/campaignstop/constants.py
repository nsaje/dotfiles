from utils.constant_base import ConstantBase


class CampaignStopState(ConstantBase):
    ACTIVE = 1
    STOPPED = 2

    _VALUES = {
        ACTIVE: 'Enabled',
        STOPPED: 'Stopped',
    }
