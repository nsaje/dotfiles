import datetime
import httplib
import operator

import codecs
import mock
import unittest

from django.test import TestCase
from django.db import DEFAULT_DB_ALIAS
from django.db import transaction
from django.conf import settings
from django.core.management import call_command


class MockDateTime(datetime.datetime):

    def __new__(cls, *args, **kwargs):
        return datetime.datetime.__new__(cls, *args, **kwargs)


class QuerySetMatcher():
    def __init__(self, obj):
        self.obj = obj

    def __eq__(self, other):
        return sorted(list(self.obj)) == sorted(list(other))


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


def format_csv_content(content):
    # Expected content - All fields are double-quoted and
    lines_formatted = []
    for line in content.split('\r\n'):
        if not line:
            continue
        fields = line.split(',')
        fields_formatted = map(lambda f: '"'+f+'"', fields)
        line_formatted = ','.join(fields_formatted)
        lines_formatted.append(line_formatted)

    formatted_content = '\r\n'.join(lines_formatted) + '\r\n'
    return formatted_content


@unittest.skipUnless(settings.RUN_REDSHIFT_UNITTESTS, 'Only run when redshift tests are enabled')
class RedshiftTestCase(TestCase):
    """
    Test case class enables testing using live Amazon Redshift instance. It can load
    fixtures that are intended for it, with a drawback that they need to be loaded
    for every test separately - the default postgres driver uses savepoints, which are
    not supported by Redshift and thus transaction rollbacks are not handeled correctly
    by Django when doing testcase wide fixtures loading.
    """
    @classmethod
    def _databases_names(cls, include_mirrors=False):
        return [DEFAULT_DB_ALIAS, settings.STATS_DB_NAME]

    @classmethod
    def _enter_atomics(cls):
        """Helper method to open atomic blocks for default database"""
        atomics = {}
        atomics[DEFAULT_DB_ALIAS] = transaction.atomic(using=DEFAULT_DB_ALIAS)
        atomics[DEFAULT_DB_ALIAS].__enter__()
        return atomics

    @classmethod
    def _rollback_atomics(cls, atomics):
        """Rollback atomic blocks opened through the previous method"""
        transaction.set_rollback(True, using=DEFAULT_DB_ALIAS)
        atomics[DEFAULT_DB_ALIAS].__exit__(None, None, None)

    def _enter_instance_atomics(self):
        """Helper method to open atomic blocks that encapsuate individual tests"""
        self._atomics = {}
        self._atomics[settings.STATS_DB_NAME] = transaction.atomic(using=settings.STATS_DB_NAME, savepoint=False)
        self._atomics[settings.STATS_DB_NAME].__enter__()

    def _rollback_instance_atomics(self):
        """Rollback atomic blocks opened through the previous method"""
        for db_alias, atomic in reversed(self._atomics.items()):
            transaction.set_rollback(True, using=db_alias)
            self._atomics[db_alias].__exit__(None, None, None)

    @classmethod
    def _fixture_database_name(cls, fixture):
        """
        Find database name from a fixture name.

        For non-default database if presumes that fixture name includes
        file extension. Fixtures for non-default database should be named
        in the following fassion: "label.db_alias.yaml"
        """

        fs = fixture.split('.')
        if len(fs) > 2 and fs[-2] in settings.DATABASES:
            return fs[-2]
        return DEFAULT_DB_ALIAS

    def setUp(self):
        self._enter_instance_atomics()

        # load fixtures for every test
        if self._instance_fixtures:
            try:

                kwargs = {
                    'verbosity': 0,
                    'interactive': False
                }

                call_command('redshift_loaddata',
                             *self._instance_fixtures,
                             **kwargs)
            except Exception:
                self._rollback_instance_atomics()
                raise

    def tearDown(self):
        self._rollback_instance_atomics()

    @classmethod
    def setUpClass(cls):
        cls.cls_atomics = cls._enter_atomics()

        if cls.fixtures:
            fixtures_by_db = {}
            for fixture in cls.fixtures:
                fixtures_by_db.setdefault(cls._fixture_database_name(fixture), []).append(fixture)

            cls._instance_fixtures = fixtures_by_db.get(settings.STATS_DB_NAME)

            for db_name, fixtures in fixtures_by_db.items():
                try:
                    if db_name == DEFAULT_DB_ALIAS:
                        call_command('loaddata', *fixtures, **{
                            'verbosity': 0,
                            'commit': False,
                            'database': db_name,
                        })
                except Exception:
                    cls._rollback_atomics(cls.cls_atomics)
                    raise
        cls.setUpTestData()
