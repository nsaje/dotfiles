from utils.constant_base import ConstantBase


class GAReportState(ConstantBase):
    FAILED = -1
    RECEIVED = 1
    PARSED = 2
    EMPTY_REPORT = 3
    SUCCESS = 4

    _VALUES = {
        FAILED: 'Failed',
        RECEIVED: 'Received',
        PARSED: 'Parsed',
        EMPTY_REPORT: 'EmptyReport',
        SUCCESS: 'Success',
    }
