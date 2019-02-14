from utils.constant_base import ConstantBase


class BidModifierType(ConstantBase):
    PUBLISHER = 1
    SOURCE = 2
    DEVICE = 3
    OPERATING_SYSTEM = 4
    PLACEMENT = 5
    COUNTRY = 6
    STATE = 7
    DMA = 8

    _VALUES = {
        PUBLISHER: "Publisher",
        SOURCE: "Source",
        DEVICE: "Device",
        OPERATING_SYSTEM: "Operating System",
        PLACEMENT: "Placement",
        COUNTRY: "Country",
        STATE: "State",
        DMA: "DMA",
    }
