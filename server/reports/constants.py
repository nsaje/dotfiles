from utils.constant_base import ConstantBase


class ReportType(ConstantBase):
    GOOGLE_ANALYTICS = 'ga'
    OMNITURE = 'omniture'

    _VALUES = {
        GOOGLE_ANALYTICS: 'Google Analytics',
        OMNITURE: 'Adobe Analytics'
    }
