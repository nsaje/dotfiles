from utils.constant_base import ConstantBase


class AdSource(ConstantBase):
    ADBLADE = 1
    GRAVITY = 2
    OUTBRAIN = 3
    YAHOO = 4
    INFOLINKS = 5
    ENGAGEYA = 6


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


class AdNetwork(ConstantBase):
    ADBLADE = 1
    GRAVITY = 2
    OUTBRAIN = 3
    YAHOO = 4
    INFOLINKS = 5
    ENGAGEYA = 6


class AdGroupNetworkSettingsState(ConstantBase):
    # keep in sync with zwei
    ACTIVE = 1
    INACTIVE = 2

    _VALUES = {
        ACTIVE: 'Enabled',
        INACTIVE: 'Paused'
    }
