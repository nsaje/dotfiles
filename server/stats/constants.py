class StructureDimension:
    ACCOUNT = "account_id"
    CAMPAIGN = "campaign_id"
    AD_GROUP = "ad_group_id"
    CONTENT_AD = "content_ad_id"
    SOURCE = "source_id"
    PUBLISHER = "publisher_id"

    _ALL = [ACCOUNT, CAMPAIGN, AD_GROUP, CONTENT_AD, SOURCE, PUBLISHER]


class DeliveryDimension:
    DEVICE = "device_type"
    DEVICE_OS = "device_os"
    DEVICE_OS_VERSION = "device_os_version"

    PLACEMENT_MEDIUM = "placement_medium"
    PLACEMENT_TYPE = "placement_type"
    VIDEO_PLAYBACK_METHOD = "video_playback_method"

    COUNTRY = "country"
    STATE = "state"
    DMA = "dma"

    AGE = "age"
    GENDER = "gender"
    AGE_GENDER = "age_gender"

    _ALL = [
        DEVICE,
        DEVICE_OS,
        DEVICE_OS_VERSION,
        PLACEMENT_MEDIUM,
        PLACEMENT_TYPE,
        VIDEO_PLAYBACK_METHOD,
        COUNTRY,
        STATE,
        DMA,
        AGE,
        GENDER,
        AGE_GENDER,
    ]

    _EXTENDED = [DEVICE_OS_VERSION, PLACEMENT_TYPE, VIDEO_PLAYBACK_METHOD, AGE, GENDER, AGE_GENDER]


class TimeDimension:
    DAY = "day"
    WEEK = "week"
    MONTH = "month"

    _ALL = [DAY, WEEK, MONTH]


# shortcuts
ACCOUNT = StructureDimension.ACCOUNT
CAMPAIGN = StructureDimension.CAMPAIGN
AD_GROUP = StructureDimension.AD_GROUP
CONTENT_AD = StructureDimension.CONTENT_AD
SOURCE = StructureDimension.SOURCE
PUBLISHER = StructureDimension.PUBLISHER


DEVICE = DeliveryDimension.DEVICE
DEVICE_OS = DeliveryDimension.DEVICE_OS
DEVICE_OS_VERSION = DeliveryDimension.DEVICE_OS_VERSION

PLACEMENT_MEDIUM = DeliveryDimension.PLACEMENT_MEDIUM
PLACEMENT_TYPE = DeliveryDimension.PLACEMENT_TYPE
VIDEO_PLAYBACK_METHOD = DeliveryDimension.VIDEO_PLAYBACK_METHOD

COUNTRY = DeliveryDimension.COUNTRY
STATE = DeliveryDimension.STATE
DMA = DeliveryDimension.DMA

AGE = DeliveryDimension.AGE
GENDER = DeliveryDimension.GENDER
AGE_GENDER = DeliveryDimension.AGE_GENDER


DAY = TimeDimension.DAY
WEEK = TimeDimension.WEEK
MONTH = TimeDimension.MONTH


class TimeLimits:
    DAY = 30
    WEEK = 30
    MONTH = 12


DimensionIdentifierMapping = {
    "account": "account_id",
    "campaign": "campaign_id",
    "ad_group": "ad_group_id",
    "content_ad": "content_ad_id",
    "source": "source_id",
    "publisher": "publisher_id",
}


IntegerDimensions = [
    StructureDimension.ACCOUNT,
    StructureDimension.CAMPAIGN,
    StructureDimension.AD_GROUP,
    StructureDimension.CONTENT_AD,
    StructureDimension.SOURCE,
    DeliveryDimension.DEVICE,
    DeliveryDimension.AGE,
    DeliveryDimension.AGE_GENDER,
    DeliveryDimension.GENDER,
]


def get_dimension_identifier(dimension):
    """
    Returns field name that identifies the dimension
    """

    return DimensionIdentifierMapping.get(dimension, dimension)


def get_dimension_name_key(dimension):
    return next((k for k, v in list(DimensionIdentifierMapping.items()) if v == dimension), dimension)


def get_delivery_dimension(breakdown):
    dimension = set(breakdown) & set(DeliveryDimension._ALL)
    if len(dimension) == 0:
        return None
    return dimension.pop()


def get_time_dimension(breakdown):
    dimension = set(breakdown) & set(TimeDimension._ALL)
    if len(dimension) == 0:
        return None
    return dimension.pop()


def get_structure_dimension(breakdown):
    breakdown = breakdown[1:]
    dimension = set(breakdown) & set(StructureDimension._ALL)

    if len(dimension) == 0:
        return None
    return dimension.pop()


def get_target_dimension(breakdown):
    if not breakdown:
        return None

    return breakdown[-1]


def get_base_dimension(breakdown):
    return breakdown[0] if breakdown else None


def get_parent_breakdown(breakdown):
    return breakdown[:-1]


def get_child_breakdown_of_dimension(breakdown, dimension):
    try:
        breakdown = breakdown[breakdown.index(dimension) + 1 :]
    except ValueError:
        pass
    return breakdown
