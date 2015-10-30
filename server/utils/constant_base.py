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
    def get_keys(cls):
        return tuple(cons for cons in cls.get_all())

    @classmethod
    def get_text(cls, cons):
        return cls._VALUES.get(cons)
