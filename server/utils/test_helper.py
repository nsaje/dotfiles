import datetime
import httplib
import operator
import mock

from django.test import TestCase
from django.db import DEFAULT_DB_ALIAS
from django.conf import settings
from django.core.management import call_command


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


class RedshiftTestCase(TestCase):

    @classmethod
    def _databases_names(cls, include_mirrors=False):
        return [DEFAULT_DB_ALIAS, settings.STATS_DB_NAME]

    @classmethod
    def _database_name(cls, fixture):
        fs = fixture.split('.')
        if len(fs) > 2 and fs[-2] in settings.DATABASES:
            return fs[-2]
        return DEFAULT_DB_ALIAS

    @classmethod
    def setUpClass(cls):
        cls.cls_atomics = cls._enter_atomics()

        if cls.fixtures:
            fixtures_by_db = {}
            for fixture in cls.fixtures:
                fixtures_by_db.setdefault(cls._database_name(fixture), []).append(fixture)
            print fixtures_by_db

            for db_name, fixtures in fixtures_by_db.items():
                try:
                    if db_name == DEFAULT_DB_ALIAS:
                        call_command('loaddata', *fixtures, **{
                            'verbosity': 0,
                            'commit': False,
                            'database': db_name,
                        })
                    elif db_name == settings.STATS_DB_NAME:
                        call_command('redshift_loaddata',
                                     *fixtures,
                                     **{
                                         'verbosity': 0,
                                     })

                except Exception:
                    cls._rollback_atomics(cls.cls_atomics)
                    raise
        try:
            cls.setUpTestData()
        except Exception:
            cls._rollback_atomics(cls.cls_atomics)
            raise
