from dash.constants import ConstantBase


class DeviceType(ConstantBase):
    """
    OpenRTB values:
    --+-----------------
    1 | Mobile/Tablet
    2 | Personal Computer
    3 | Connected TV
    4 | Phone
    5 | Tablet
    6 | Connected Device
    7 | Set Top Box
    """

    UNKNOWN = 0
    MOBILE = 1
    PC = 2
    TV = 3
    PHONE = 4
    TABLET = 5
    CONNECTED = 6
    SET_TOP_BOX = 7

    _VALUES = {
        UNKNOWN: 'Not reported',
        MOBILE: 'Mobile',
        PC: 'Desktop',
        TV: 'TV',
        PHONE: 'Phone',
        TABLET: 'Tablet',
        CONNECTED: 'Connected',
        SET_TOP_BOX: 'SetTop Box',
    }
