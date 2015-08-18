from utils.constant_base import ConstantBase
from dash import regions


class AdGroupSettingsState(ConstantBase):
    ACTIVE = 1
    INACTIVE = 2

    _VALUES = {
        ACTIVE: 'Enabled',
        INACTIVE: 'Paused'
    }


class AdGroupSourceSettingsState(ConstantBase):
    # keep in sync with zwei
    ACTIVE = 1
    INACTIVE = 2

    _VALUES = {
        ACTIVE: 'Enabled',
        INACTIVE: 'Paused'
    }


class AdTargetDevice(ConstantBase):
    DESKTOP = 'desktop'
    MOBILE = 'mobile'

    _VALUES = {
        DESKTOP: 'Desktop',
        MOBILE: 'Mobile'
    }


class AdTargetLocation(ConstantBase):
    _VALUES = dict(regions.COUNTRY_BY_CODE.items() + regions.DMA_BY_CODE.items())

    @classmethod
    def get_choices(cls):
        return cls._VALUES.items()


class ContentAdSubmissionStatus(ConstantBase):
    NOT_SUBMITTED = -1
    PENDING = 1
    APPROVED = 2
    REJECTED = 3
    LIMIT_REACHED = 4

    _VALUES = {
        NOT_SUBMITTED: 'Not submitted',
        PENDING: 'Pending',
        APPROVED: 'Approved',
        REJECTED: 'Rejected',
        LIMIT_REACHED: 'Limit reached',
    }


class ContentAdSourceState(ConstantBase):
    ACTIVE = 1
    INACTIVE = 2

    _VALUES = {
        ACTIVE: 'Enabled',
        INACTIVE: 'Paused'
    }


class IABCategory(ConstantBase):
    IAB1 = 'IAB1'
    IAB2 = 'IAB2'
    IAB3 = 'IAB3'
    IAB4 = 'IAB4'
    IAB5 = 'IAB5'
    IAB6 = 'IAB6'
    IAB7 = 'IAB7'
    IAB8 = 'IAB8'
    IAB9 = 'IAB9'
    IAB10 = 'IAB10'
    IAB11 = 'IAB11'
    IAB12 = 'IAB12'
    IAB13 = 'IAB13'
    IAB14 = 'IAB14'
    IAB15 = 'IAB15'
    IAB16 = 'IAB16'
    IAB17 = 'IAB17'
    IAB18 = 'IAB18'
    IAB19 = 'IAB19'
    IAB20 = 'IAB20'
    IAB21 = 'IAB21'
    IAB22 = 'IAB22'
    IAB23 = 'IAB23'
    IAB24 = 'IAB24'

    _VALUES = {
        IAB1: 'IAB1 - Arts & Entertainment',
        IAB2: 'IAB2 - Automotive',
        IAB3: 'IAB3 - Business',
        IAB4: 'IAB4 - Careers',
        IAB5: 'IAB5 - Education',
        IAB6: 'IAB6 - Family & Parenting',
        IAB7: 'IAB7 - Health & Fitness',
        IAB8: 'IAB8 - Food & Drink',
        IAB9: 'IAB9 - Hobbies & Interests',
        IAB10: 'IAB10 - Home & Garden',
        IAB11: 'IAB11 - Law, Government & Politics',
        IAB12: 'IAB12 - News',
        IAB13: 'IAB13 - Personal Finance',
        IAB14: 'IAB14 - Society',
        IAB15: 'IAB15 - Science',
        IAB16: 'IAB16 - Pets',
        IAB17: 'IAB17 - Sports',
        IAB18: 'IAB18 - Style & Fashion',
        IAB19: 'IAB19 - Technology & Computing',
        IAB20: 'IAB20 - Travel',
        IAB21: 'IAB21 - Real Estate',
        IAB22: 'IAB22 - Shopping',
        IAB23: 'IAB23 - Religion & Spirituality',
        IAB24: 'IAB24 - Uncategorized',
    }


class PromotionGoal(ConstantBase):
    BRAND_BUILDING = 1
    TRAFFIC_ACQUISITION = 2
    CONVERSIONS = 3

    _VALUES = {
        BRAND_BUILDING: 'Brand Building',
        TRAFFIC_ACQUISITION: 'Traffic Acquisition',
        CONVERSIONS: 'Conversions'
    }


class SourceAction(ConstantBase):
    CAN_UPDATE_STATE = 1
    CAN_UPDATE_CPC = 2
    CAN_UPDATE_DAILY_BUDGET_AUTOMATIC = 3
    CAN_MANAGE_CONTENT_ADS = 4
    HAS_3RD_PARTY_DASHBOARD = 5
    CAN_MODIFY_START_DATE = 6
    CAN_MODIFY_END_DATE = 7
    CAN_MODIFY_DEVICE_TARGETING = 8
    CAN_MODIFY_TRACKING_CODES = 9
    CAN_MODIFY_AD_GROUP_NAME = 10
    CAN_MODIFY_AD_GROUP_IAB_CATEGORY_AUTOMATIC = 11
    UPDATE_TRACKING_CODES_ON_CONTENT_ADS = 12
    CAN_UPDATE_DAILY_BUDGET_MANUAL = 13
    CAN_MODIFY_AD_GROUP_IAB_CATEGORY_MANUAL = 14
    CAN_MODIFY_DMA_TARGETING_AUTOMATIC = 15
    CAN_MODIFY_COUNTRY_TARGETING = 16
    CAN_MODIFY_DMA_TARGETING_MANUAL = 17

    _VALUES = {
        CAN_UPDATE_STATE: 'Can update state',
        CAN_UPDATE_CPC: 'Can update CPC',
        CAN_UPDATE_DAILY_BUDGET_AUTOMATIC: 'Can update daily budget automatically',
        CAN_MANAGE_CONTENT_ADS: 'Can manage content ads',
        HAS_3RD_PARTY_DASHBOARD: 'Has 3rd party dashboard',
        CAN_MODIFY_START_DATE: 'Can modify start date',
        CAN_MODIFY_END_DATE: 'Can modify end date',
        CAN_MODIFY_DEVICE_TARGETING: 'Can modify device targeting',
        CAN_MODIFY_DMA_TARGETING_AUTOMATIC: 'Can modify DMA targeting automatically',
        CAN_MODIFY_DMA_TARGETING_MANUAL: 'Can modify DMA targeting manually',
        CAN_MODIFY_COUNTRY_TARGETING: 'Can modify targeting by country',
        CAN_MODIFY_TRACKING_CODES: 'Can modify tracking codes',
        CAN_MODIFY_AD_GROUP_NAME: 'Can modify adgroup name',
        CAN_MODIFY_AD_GROUP_IAB_CATEGORY_AUTOMATIC: 'Can modify ad group IAB category automatically',
        UPDATE_TRACKING_CODES_ON_CONTENT_ADS: 'Update tracking codes on content ads',
        CAN_UPDATE_DAILY_BUDGET_MANUAL: 'Can update daily budget manually',
        CAN_MODIFY_AD_GROUP_IAB_CATEGORY_MANUAL: 'Can modify ad group IAB category manually',
    }


class SourceSubmissionType(ConstantBase):
    DEFAULT = 1
    AD_GROUP = 2
    BATCH = 3

    _VALUES = {
        DEFAULT: 'Default',
        AD_GROUP: 'One submission per ad group',
        BATCH: 'Submit whole batch at once'
    }


class SourceType(ConstantBase):
    ADBLADE = 'adblade'
    GRAVITY = 'gravity'
    NRELATE = 'nrelate'
    OUTBRAIN = 'outbrain'
    YAHOO = 'yahoo'
    ZEMANTA = 'zemanta'
    DISQUS = 'disqus'
    B1 = 'b1'

    _VALUES = {
        ADBLADE: 'AdBlade',
        GRAVITY: 'Gravity',
        NRELATE: 'nRelate',
        OUTBRAIN: 'Outbrain',
        YAHOO: 'Yahoo',
        ZEMANTA: 'Zemanta',
        B1: 'B1'
    }


class ConversionPixelStatus(ConstantBase):
    NOT_USED = 1
    INACTIVE = 2
    ACTIVE = 3

    _VALUES = {
        NOT_USED: 'Not used',
        INACTIVE: 'Inactive',
        ACTIVE: 'Active',
    }


class UploadBatchStatus(ConstantBase):
    DONE = 1
    FAILED = 2
    IN_PROGRESS = 3

    _VALUES = {
        DONE: 'Done',
        FAILED: 'Failed',
        IN_PROGRESS: 'In progress'
    }
