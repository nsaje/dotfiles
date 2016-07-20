class StructureDimension:
    ACCOUNT = 'account_id'
    CAMPAIGN = 'campaign_id'
    AD_GROUP = 'ad_group_id'
    CONTENT_AD = 'content_ad_id'
    SOURCE = 'source_id'
    PUBLISHER = 'publisher'

    _ALL = [ACCOUNT, CAMPAIGN, AD_GROUP, CONTENT_AD, SOURCE, PUBLISHER]


class DeliveryDimension:
    DEVICE = 'device_type'
    COUNTRY = 'country'
    STATE = 'state'
    DMA = 'dma'
    AGE = 'age'
    GENDER = 'gender'
    AGE_GENDER = 'age_gender'

    _ALL = [DEVICE, COUNTRY, STATE, DMA, AGE, GENDER, AGE_GENDER]


class TimeDimension:
    DAY = 'day'
    WEEK = 'week'
    MONTH = 'month'

    _ALL = [DAY, WEEK, MONTH]


class TimeLimits:
    DAY = 30
    WEEK = 30
    MONTH = 12


DimensionIdentifierMapping = {
    'account': 'account_id',
    'campaign': 'campaign_id',
    'ad_group': 'ad_group_id',
    'content_ad': 'content_ad_id',
    'source': 'source_id',
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


SpecialDimensionNameKeys = {
    StructureDimension.ACCOUNT: 'account_name',
    StructureDimension.CAMPAIGN: 'campaign_name',
    StructureDimension.AD_GROUP: 'ad_group_name',
    StructureDimension.CONTENT_AD: 'content_ad_title',
    StructureDimension.SOURCE: 'source_name',
}


def get_dimension_identifier(dimension):
    """
    Returns field name that identifies the dimension
    """

    return DimensionIdentifierMapping.get(dimension, dimension)


def get_dimension_name_key(dimension):
    if dimension in SpecialDimensionNameKeys:
        return SpecialDimensionNameKeys[dimension]
    return dimension


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


def get_level_dimension(constraints):
    dimensions = [
        StructureDimension.AD_GROUP,
        StructureDimension.CAMPAIGN,
        StructureDimension.ACCOUNT
    ]

    for d in dimensions:
        if d in constraints.keys():
            return d

    return None


def get_target_dimension(breakdown):
    return breakdown[-1]


def get_base_dimension(breakdown):
    return breakdown[0] if breakdown else None


def get_parent_breakdown(breakdown):
    return breakdown[:-1]
