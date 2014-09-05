import datetime
import operator


class MockDateTime(datetime.datetime):

    def __new__(cls, *args, **kwargs):
        return datetime.datetime.__new__(cls, *args, **kwargs)


def dicts_match_for_keys(dct1, dct2, keys):
    if not reduce(operator.iand, (k in dct1 and k in dct2 for k in keys), True):
        return False
    return reduce(operator.iand, (dct1[k] == dct2[k] for k in keys), True)


def sequence_of_dicts_match_for_keys(dicts1, dicts2, keys):
    if len(dicts1) != len(dicts2):
        return False
    return reduce(operator.iand, 
        (dicts_match_for_keys(dct1, dct2, keys) for dct1, dct2 in zip(dicts1, dicts2)),
        True)
