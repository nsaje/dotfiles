import datetime
import json
import unittest

import pytz

from utils import json_helper


class JsonHelperTestCase(unittest.TestCase):
    def test_naive_datetime(self):
        test_datetime = datetime.datetime(2014, 11, 1, 18, 0, 0)
        test_obj = {
            'id': 100,
            'test': 'something',
            'datetime': test_datetime
        }

        expected = '{"test": "something", "id": 100, "datetime": "2014-11-01T18:00:00"}'
        self.assertEqual(json.dumps(test_obj, cls=json_helper.JSONEncoder), expected)

    def test_naive_date(self):
        test_datetime = datetime.datetime(2014, 11, 1, 18, 0, 0)
        test_obj = {
            'id': 100,
            'test': 'something',
            'datetime': test_datetime.date()
        }

        expected = '{"test": "something", "id": 100, "datetime": "2014-11-01"}'
        self.assertEqual(json.dumps(test_obj, cls=json_helper.JSONEncoder), expected)

    def test_naive_time(self):
        test_datetime = datetime.datetime(2014, 11, 1, 18, 0, 0)
        test_obj = {
            'id': 100,
            'test': 'something',
            'datetime': test_datetime.time()
        }

        expected = '{"test": "something", "id": 100, "datetime": "18:00:00"}'
        self.assertEqual(json.dumps(test_obj, cls=json_helper.JSONEncoder), expected)

    def test_aware_datetime(self):
        test_datetime = datetime.datetime(2014, 11, 1, 18, 0, 0)
        test_datetime = test_datetime.replace(tzinfo=pytz.utc)
        test_obj = {
            'id': 100,
            'test': 'something',
            'datetime': test_datetime
        }

        expected = '{"test": "something", "id": 100, "datetime": "2014-11-01T18:00:00+00:00"}'
        self.assertEqual(json.dumps(test_obj, cls=json_helper.JSONEncoder), expected)

    def test_aware_date(self):
        test_datetime = datetime.datetime(2014, 11, 1, 18, 0, 0)
        test_obj = {
            'id': 100,
            'test': 'something',
            'datetime': test_datetime.date()
        }

        expected = '{"test": "something", "id": 100, "datetime": "2014-11-01"}'
        self.assertEqual(json.dumps(test_obj, cls=json_helper.JSONEncoder), expected)

    def test_aware_time(self):
        test_datetime = datetime.datetime(2014, 11, 1, 18, 0, 0)
        test_obj = {
            'id': 100,
            'test': 'something',
            'datetime': test_datetime.time()
        }

        expected = '{"test": "something", "id": 100, "datetime": "18:00:00"}'
        self.assertEqual(json.dumps(test_obj, cls=json_helper.JSONEncoder), expected)
