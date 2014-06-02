class ConstantBase(object):
    @classmethod
    def get_all(cls):
        result = []

        for attr in vars(cls):
            if attr[:2] != '__' and attr[-2:] != '__':
                candidate = getattr(cls, attr)
                if not hasattr(candidate, '__call__'):
                    result.append(candidate)

        return result

    @classmethod
    def get_choices(cls):
        return ((id, cls.get_text(id)) for id in cls.get_all())


class AdGroupSettingsStatus(ConstantBase):
    ACTIVE = 1
    INACTIVE = 2

    @classmethod
    def get_text(cls, status):
        if status == cls.ACTIVE:
            return 'Active'
        elif status == cls.INACTIVE:
            return 'Inactive'
        else:
            raise Exception('Unknown campaign status %s.' % str(status))


class AdGroupNetworkSettingsStatus(ConstantBase):
    ACTIVE = 1
    INACTIVE = 2

    @classmethod
    def get_text(cls, status):
        if status == cls.ACTIVE:
            return 'Active'
        elif status == cls.INACTIVE:
            return 'Inactive'
        else:
            raise Exception('Unknown campaign status %s.' % str(status))
