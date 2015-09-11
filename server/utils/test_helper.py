import datetime
import httplib
import operator
import mock


class MockDateTime(datetime.datetime):

    def __new__(cls, *args, **kwargs):
        return datetime.datetime.__new__(cls, *args, **kwargs)


class QuerySetMatcher():
    def __init__(self, obj):
        self.obj = obj

    def __eq__(self, other):
        return list(self.obj) == list(other)


class ListMatcher():
    """Checks if both lists contain the same elements.
    For use with Mock.assert_called_with()."""

    def __init__(self, obj):
        self.obj = obj

    def __eq__(self, other):
        return sorted(self.obj) == sorted(other)


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
    return reduce(
        operator.iand,
        (dicts_match_for_keys(dct1, dct2, keys) for dct1, dct2 in zip(dicts1, dicts2)),
        True)


def prepare_mock_urlopen(mock_urlopen, exception=None):
    if exception:
        mock_urlopen.side_effect = exception
        return

    mock_request = mock.Mock()
    mock_request.status_code = httplib.OK
    mock_urlopen.return_value = mock_request
