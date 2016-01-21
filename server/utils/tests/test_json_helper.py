import datetime
import json
import unittest

import pytz

from utils import json_helper


class JsonHelperTestCase(unittest.TestCase):
    def setUp(self):
        self.timezone = 'America/New_York'

    def _get_test_object(self, test_datetime):
        return {
            'id': 100,
            'test': 'something',
            'datetime': test_datetime
        }

    def test_naive_datetime(self):
        test_datetime = datetime.datetime(2014, 11, 1, 18, 0, 0)
        test_obj = self._get_test_object(test_datetime)

        result = json.dumps(
            test_obj,
            cls=json_helper.JSONEncoder,
            convert_datetimes_tz=self.timezone
        )

        expected = '{"test": "something", "id": 100, "datetime": "2014-11-01T14:00:00"}'

        self.assertEqual(result, expected)

    def test_naive_datetime_no_convert(self):
        test_datetime = datetime.datetime(2014, 11, 1, 18, 0, 0)
        test_obj = self._get_test_object(test_datetime)

        result = json.dumps(
            test_obj,
            cls=json_helper.JSONEncoder
        )

        expected = '{"test": "something", "id": 100, "datetime": "2014-11-01T18:00:00"}'

        self.assertEqual(result, expected)

    def test_naive_datetime_dst(self):
        test_datetime = datetime.datetime(2014, 1, 1, 18, 0, 0)
        test_obj = self._get_test_object(test_datetime)

        result = json.dumps(
            test_obj,
            cls=json_helper.JSONEncoder,
            convert_datetimes_tz=self.timezone
        )

        expected = '{"test": "something", "id": 100, "datetime": "2014-01-01T13:00:00"}'

        self.assertEqual(result, expected)

    def test_naive_date(self):
        test_datetime = datetime.datetime(2014, 11, 1, 18, 0, 0)
        test_obj = self._get_test_object(test_datetime.date())

        expected = '{"test": "something", "id": 100, "datetime": "2014-11-01"}'
        self.assertEqual(json.dumps(test_obj, cls=json_helper.JSONEncoder), expected)

    def test_naive_time(self):
        test_datetime = datetime.datetime(2014, 11, 1, 18, 0, 0)
        test_obj = self._get_test_object(test_datetime.time())

        expected = '{"test": "something", "id": 100, "datetime": "18:00:00"}'
        self.assertEqual(json.dumps(test_obj, cls=json_helper.JSONEncoder), expected)

    def test_aware_datetime(self):
        test_datetime = datetime.datetime(2014, 11, 1, 18, 0, 0)
        test_datetime = test_datetime.replace(tzinfo=pytz.utc)
        test_obj = self._get_test_object(test_datetime)

        result = json.dumps(
            test_obj,
            cls=json_helper.JSONEncoder,
            convert_datetimes_tz=self.timezone
        )

        expected = '{"test": "something", "id": 100, "datetime": "2014-11-01T14:00:00"}'

        self.assertEqual(result, expected)

    def test_aware_datetime_localized(self):
        test_datetime = datetime.datetime(2014, 12, 1, 18, 0, 0)
        test_datetime = pytz.timezone('Europe/Ljubljana').localize(test_datetime)
        test_obj = self._get_test_object(test_datetime)

        result = json.dumps(
            test_obj,
            cls=json_helper.JSONEncoder,
            convert_datetimes_tz=self.timezone
        )

        expected = '{"test": "something", "id": 100, "datetime": "2014-12-01T12:00:00"}'

        self.assertEqual(result, expected)

    def test_aware_date(self):
        test_datetime = datetime.datetime(2014, 11, 1, 18, 0, 0)
        test_datetime = test_datetime.replace(tzinfo=pytz.utc)
        test_obj = self._get_test_object(test_datetime.date())

        expected = '{"test": "something", "id": 100, "datetime": "2014-11-01"}'
        self.assertEqual(json.dumps(test_obj, cls=json_helper.JSONEncoder), expected)

    def test_aware_time(self):
        test_datetime = datetime.datetime(2014, 11, 1, 18, 0, 0)
        test_datetime = test_datetime.replace(tzinfo=pytz.utc)
        test_obj = self._get_test_object(test_datetime.time())

        expected = '{"test": "something", "id": 100, "datetime": "18:00:00"}'
        self.assertEqual(json.dumps(test_obj, cls=json_helper.JSONEncoder), expected)


class DateJSONEncoderTestCase(unittest.TestCase):

    def test_encode_date(self):
        result = json.dumps({'date': datetime.date(2016, 1, 1)}, cls=json_helper.DateJSONEncoder)
        self.assertEqual('{"date": "2016-01-01"}', result)

    def test_encode_datetime_fail(self):
        with self.assertRaises(TypeError):
            json.dumps({'date': datetime.datetime(2016, 1, 1)}, cls=json_helper.DateJSONEncoder)
