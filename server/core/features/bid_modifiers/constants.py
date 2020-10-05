from utils.constant_base import ConstantBase

UNSUPPORTED_TARGETS = [None, "Other"]


class BidModifierType(ConstantBase):
    PUBLISHER = 1
    SOURCE = 2
    DEVICE = 3
    OPERATING_SYSTEM = 4
    ENVIRONMENT = 5
    COUNTRY = 6
    STATE = 7
    DMA = 8
    AD = 9
    DAY_HOUR = 10
    PLACEMENT = 11
    BROWSER = 12
    CONNECTION_TYPE = 13

    _VALUES = {
        PUBLISHER: "Publisher",
        SOURCE: "Source",
        DEVICE: "Device",
        OPERATING_SYSTEM: "Operating System",
        ENVIRONMENT: "Environment",
        COUNTRY: "Country",
        STATE: "State",
        DMA: "DMA",
        AD: "Ad",
        DAY_HOUR: "Day - Hour",
        PLACEMENT: "Placement",
        BROWSER: "Browser",
        CONNECTION_TYPE: "Connection Type",
    }
