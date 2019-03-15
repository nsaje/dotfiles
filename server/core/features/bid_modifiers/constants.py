import stats.constants
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
    AD = 9

    _VALUES = {
        PUBLISHER: "Publisher",
        SOURCE: "Source",
        DEVICE: "Device",
        OPERATING_SYSTEM: "Operating System",
        PLACEMENT: "Placement",
        COUNTRY: "Country",
        STATE: "State",
        DMA: "DMA",
        AD: "Ad",
    }


BidModifierTypeToDeliveryDimensionMap = {
    BidModifierType.DEVICE: stats.constants.DeliveryDimension.DEVICE,
    BidModifierType.OPERATING_SYSTEM: stats.constants.DeliveryDimension.DEVICE_OS,
    BidModifierType.PLACEMENT: stats.constants.DeliveryDimension.PLACEMENT_MEDIUM,
    BidModifierType.COUNTRY: stats.constants.DeliveryDimension.COUNTRY,
    BidModifierType.STATE: stats.constants.DeliveryDimension.STATE,
    BidModifierType.DMA: stats.constants.DeliveryDimension.DMA,
}

DeliveryDimensionToBidModifierTypeMap = dict((reversed(item) for item in BidModifierTypeToDeliveryDimensionMap.items()))
