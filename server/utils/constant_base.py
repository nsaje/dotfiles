class ConstantBase(object):
    @classmethod
    def _get_all_kv_pairs(cls):
        result = []

        for attr in vars(cls):
            if attr[:1] != "_" and attr[:2] != "__" and attr[-2:] != "__":
                candidate = getattr(cls, attr)
                if not hasattr(candidate, "__call__"):
                    result.append((attr, candidate))

        return result

    @classmethod
    def get_all(cls):
        return [value for key, value in cls._get_all_kv_pairs()]

    @classmethod
    def get_all_names(cls):
        return [key for key, value in cls._get_all_kv_pairs()]

    @classmethod
    def get_choices(cls):
        return ((cons, cls.get_text(cons)) for cons in cls.get_all())

    @classmethod
    def get_name(cls, value):
        return {v: k for k, v in cls._get_all_kv_pairs()}[value]

    @classmethod
    def get_text(cls, cons):
        return cls._VALUES.get(cons)

    @classmethod
    def get_value(cls, name):
        return {v: k for k, v in cls._VALUES.items()}.get(name)

    @classmethod
    def get_value_from_name(cls, name):
        return dict(cls._get_all_kv_pairs()).get(name)
