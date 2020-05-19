import dash.constants
from core.features import bid_modifiers

NOT_REPORTED = "Not reported"


class StructureDimension:
    ACCOUNT = "account_id"
    CAMPAIGN = "campaign_id"
    AD_GROUP = "ad_group_id"
    CONTENT_AD = "content_ad_id"
    SOURCE = "source_id"
    PUBLISHER = "publisher_id"
    PLACEMENT = "placement_id"

    _ALL = [ACCOUNT, CAMPAIGN, AD_GROUP, CONTENT_AD, SOURCE, PUBLISHER, PLACEMENT]


class DeliveryDimension:
    DEVICE = "device_type"
    DEVICE_OS = "device_os"
    DEVICE_OS_VERSION = "device_os_version"

    ENVIRONMENT = "environment"
    ZEM_PLACEMENT_TYPE = "zem_placement_type"
    PLACEMENT_TYPE = "placement_type"
    VIDEO_PLAYBACK_METHOD = "video_playback_method"

    COUNTRY = "country"
    REGION = "region"
    DMA = "dma"

    AGE = "age"
    GENDER = "gender"
    AGE_GENDER = "age_gender"

    _ALL = [
        DEVICE,
        DEVICE_OS,
        DEVICE_OS_VERSION,
        ENVIRONMENT,
        ZEM_PLACEMENT_TYPE,
        PLACEMENT_TYPE,
        VIDEO_PLAYBACK_METHOD,
        COUNTRY,
        REGION,
        DMA,
        AGE,
        GENDER,
        AGE_GENDER,
    ]

    _EXTENDED = [DEVICE_OS_VERSION, ZEM_PLACEMENT_TYPE, VIDEO_PLAYBACK_METHOD, AGE, GENDER, AGE_GENDER]
    _PLACEMENT = [PLACEMENT_TYPE]


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
PLACEMENT = StructureDimension.PLACEMENT

DEVICE = DeliveryDimension.DEVICE
DEVICE_OS = DeliveryDimension.DEVICE_OS
DEVICE_OS_VERSION = DeliveryDimension.DEVICE_OS_VERSION

ENVIRONMENT = DeliveryDimension.ENVIRONMENT
ZEM_PLACEMENT_TYPE = DeliveryDimension.ZEM_PLACEMENT_TYPE
PLACEMENT_TYPE = DeliveryDimension.PLACEMENT_TYPE
VIDEO_PLAYBACK_METHOD = DeliveryDimension.VIDEO_PLAYBACK_METHOD

COUNTRY = DeliveryDimension.COUNTRY
REGION = DeliveryDimension.REGION
DMA = DeliveryDimension.DMA

AGE = DeliveryDimension.AGE
GENDER = DeliveryDimension.GENDER
AGE_GENDER = DeliveryDimension.AGE_GENDER

DAY = TimeDimension.DAY
WEEK = TimeDimension.WEEK
MONTH = TimeDimension.MONTH

PLACEMENT_DIMENSIONS = [StructureDimension.PLACEMENT] + DeliveryDimension._PLACEMENT


class TimeLimits:
    DAY = 30
    WEEK = 30
    MONTH = 12


class DimensionIdentifier:
    ACCOUNT = "account"
    CAMPAIGN = "campaign"
    AD_GROUP = "ad_group"
    CONTENT_AD = "content_ad"
    SOURCE = "source"
    PUBLISHER = "publisher"
    PLACEMENT = "placement"


DimensionIdentifierMapping = {
    DimensionIdentifier.ACCOUNT: "account_id",
    DimensionIdentifier.CAMPAIGN: "campaign_id",
    DimensionIdentifier.AD_GROUP: "ad_group_id",
    DimensionIdentifier.CONTENT_AD: "content_ad_id",
    DimensionIdentifier.SOURCE: "source_id",
    DimensionIdentifier.PUBLISHER: "publisher_id",
    DimensionIdentifier.PLACEMENT: "placement_id",
}


DeliveryDimensionConstantClassMap = {
    DeliveryDimension.DEVICE: dash.constants.DeviceType,
    DeliveryDimension.DEVICE_OS: dash.constants.OperatingSystem,
    DeliveryDimension.ENVIRONMENT: dash.constants.Environment,
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


def contains_dimension(breakdown, dimensions):
    if not (breakdown and dimensions):
        return False
    return len(set(breakdown) & set(dimensions)) != 0


def is_extended_delivery_dimension(dimension):
    return dimension in DeliveryDimension._EXTENDED


def is_top_level_delivery_dimension(dimension):
    return dimension in set(DeliveryDimension._ALL) - set(DeliveryDimension._EXTENDED) - set(
        DeliveryDimension._PLACEMENT
    )


def is_placement_breakdown(breakdown):
    return any(dimension in breakdown for dimension in PLACEMENT_DIMENSIONS)


def get_top_level_delivery_dimensions():
    return [
        dimension
        for dimension in DeliveryDimension._ALL
        if dimension not in DeliveryDimension._EXTENDED + DeliveryDimension._PLACEMENT
    ]


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


TargetDimensionToBidModifierTypeMap = {
    StructureDimension.PUBLISHER: bid_modifiers.BidModifierType.PUBLISHER,
    StructureDimension.SOURCE: bid_modifiers.BidModifierType.SOURCE,
    DeliveryDimension.DEVICE: bid_modifiers.BidModifierType.DEVICE,
    DeliveryDimension.DEVICE_OS: bid_modifiers.BidModifierType.OPERATING_SYSTEM,
    DeliveryDimension.ENVIRONMENT: bid_modifiers.BidModifierType.ENVIRONMENT,
    DeliveryDimension.COUNTRY: bid_modifiers.BidModifierType.COUNTRY,
    DeliveryDimension.REGION: bid_modifiers.BidModifierType.STATE,
    DeliveryDimension.DMA: bid_modifiers.BidModifierType.DMA,
    StructureDimension.CONTENT_AD: bid_modifiers.BidModifierType.AD,
    StructureDimension.PLACEMENT: bid_modifiers.BidModifierType.PLACEMENT,
}
