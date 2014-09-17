import datetime
import operator


class MockDateTime(datetime.datetime):

    def __new__(cls, *args, **kwargs):
        return datetime.datetime.__new__(cls, *args, **kwargs)


def is_equal(val1, val2):
    if isinstance(val1, float) or isinstance(val2, float):
        return round(val1, 4) == round(val2, 4)
    else:
        return val1 == val2


def dicts_match_for_keys(dct1, dct2, keys):
    if not reduce(operator.iand, (k in dct1 and k in dct2 for k in keys), True):
        return False
    return reduce(operator.iand, (is_equal(dct1[k], dct2[k]) for k in keys), True)


def sequence_of_dicts_match_for_keys(dicts1, dicts2, keys):
    if len(dicts1) != len(dicts2):
        return False
    return reduce(operator.iand, 
        (dicts_match_for_keys(dct1, dct2, keys) for dct1, dct2 in zip(dicts1, dicts2)),
        True)
