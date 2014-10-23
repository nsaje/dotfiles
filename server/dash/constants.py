from decimal import Decimal
from utils.constant_base import ConstantBase


class AdGroupSettingsState(ConstantBase):
    ACTIVE = 1
    INACTIVE = 2
    ARCHIVED = 3

    _VALUES = {
        ACTIVE: 'Enabled',
        INACTIVE: 'Paused',
        ARCHIVED: 'Archived'
    }

    @classmethod
    def get_all(cls):
        # Archived not included because it should not validate on ad group settings state,
        # it's intended to be manually set when returning response to the UI
        return [cls.ACTIVE, cls.INACTIVE]


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


class AdTargetCountry(ConstantBase):
    AUSTRALIA = 'AU'
    CANADA = 'CA'
    IRELAND = 'IE'
    NEW_ZAELAND = 'NZ'
    UNITED_KINGDOM = 'UK'
    UNITED_STATES = 'US'

    _VALUES = {
        AUSTRALIA: 'Australia',
        CANADA: 'Canada',
        IRELAND: 'Ireland',
        NEW_ZAELAND: 'New Zealand',
        UNITED_KINGDOM: 'United Kingdom',
        UNITED_STATES: 'United States'
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


class SourceType(ConstantBase):
    ADBLADE = 'adblade'
    GRAVITY = 'gravity'
    NRELATE = 'nrelate'
    OUTBRAIN = 'outbrain'
    YAHOO = 'yahoo'
    ZEMANTA = 'zemanta'

    _VALUES = {
        ADBLADE: 'AdBlade',
        GRAVITY: 'Gravity',
        NRELATE: 'nRelate',
        OUTBRAIN: 'Outbrain',
        YAHOO: 'Yahoo',
        ZEMANTA: 'Zemanta'
    }
