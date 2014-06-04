class ConstantBase(object):
    @classmethod
    def get_all(cls):
        result = []

        for attr in vars(cls):
            if attr[:1] != '_' and attr[:2] != '__' and attr[-2:] != '__':
                candidate = getattr(cls, attr)
                if not hasattr(candidate, '__call__'):
                    result.append(candidate)

        return result

    @classmethod
    def get_choices(cls):
        return ((cons, cls.get_text(cons)) for cons in cls.get_all())

    @classmethod
    def get_text(cls, cons):
        return cls._VALUES.get(cons)


class AdNetwork(ConstantBase):
    ADBLADE = 'adblade'
    GRAVITY = 'gravity'
    OUTBRAIN = 'outbrain'
    TABOOLA = 'taboola'
    YAHOO = 'yahoo'


class AdGroupSettingsState(ConstantBase):
    ACTIVE = 1
    INACTIVE = 2

    _VALUES = {
        ACTIVE: 'Active',
        INACTIVE: 'Inactive'
    }


class AdGroupNetworkSettingsState(ConstantBase):
    ACTIVE = 1
    INACTIVE = 2

    _VALUES = {
        ACTIVE: 'Active',
        INACTIVE: 'Inactive'
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
