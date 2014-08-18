from decimal import Decimal
from utils.constant_base import ConstantBase


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
        DESKTOP: 'Destkop',
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


class ServiceFee(ConstantBase):
    FEE_1500 = Decimal('0.1500')
    FEE_2000 = Decimal('0.2000')
    FEE_2050 = Decimal('0.2050')
    FEE_2233 = Decimal('0.2233')
    FEE_2500 = Decimal('0.2500')

    _VALUES = {
        FEE_1500: '15%',
        FEE_2000: '20%',
        FEE_2050: '20.5%',
        FEE_2233: '22.33%',
        FEE_2500: '25%'
    }


class IABCategory(ConstantBase):
    IAB_1 = 1
    IAB_2 = 2
    IAB_3 = 3
    IAB_4 = 4
    IAB_5 = 5
    IAB_6 = 6
    IAB_7 = 7
    IAB_8 = 8
    IAB_9 = 9
    IAB_10 = 10
    IAB_11 = 11
    IAB_12 = 12
    IAB_13 = 13
    IAB_14 = 14
    IAB_15 = 15
    IAB_16 = 16
    IAB_17 = 17
    IAB_18 = 18
    IAB_19 = 19
    IAB_20 = 20
    IAB_21 = 21
    IAB_22 = 22
    IAB_23 = 23
    IAB_24 = 24

    _VALUES = {
        IAB_1: 'Arts & Entertainment',
        IAB_2: 'Automotive',
        IAB_3: 'Business',
        IAB_4: 'Careers',
        IAB_5: 'Education',
        IAB_6: 'Family & Parenting',
        IAB_7: 'Health & Fitness',
        IAB_8: 'Food & Drink',
        IAB_9: 'Hobbies & Interests',
        IAB_10: 'Home & Garden',
        IAB_11: 'Law, Government & Politics',
        IAB_12: 'News',
        IAB_13: 'Personal Finance',
        IAB_14: 'Society',
        IAB_15: 'Science',
        IAB_16: 'Pets',
        IAB_17: 'Sports',
        IAB_18: 'Style & Fashion',
        IAB_19: 'Technology & Computing',
        IAB_20: 'Travel',
        IAB_21: 'Real Estate',
        IAB_22: 'Shopping',
        IAB_23: 'Religion & Spirituality',
        IAB_24: 'Uncategorized',
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
