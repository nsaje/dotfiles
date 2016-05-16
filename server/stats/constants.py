

class StructureDimension:
    ACCOUNT = 'account'
    CAMPAIGN = 'campaign'
    AD_GROUP = 'ad_group'
    CONTENT_AD = 'content_ad'
    SOURCE = 'source'
    PUBLISHER = 'publisher'

    _ALL = [ACCOUNT, CAMPAIGN, AD_GROUP, CONTENT_AD, SOURCE, PUBLISHER]


class DeliveryDimension:
    DEVICE = 'device'
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


IntegerDimensions = [
    StructureDimension.ACCOUNT,
    StructureDimension.CAMPAIGN,
    StructureDimension.AD_GROUP,
    StructureDimension.CONTENT_AD,
    StructureDimension.SOURCE,
    DeliveryDimension.DEVICE,
]


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
    return breakdown[-1]


def get_base_dimension(breakdown):
    return breakdown[0]
