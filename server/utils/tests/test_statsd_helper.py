import unittest

import mock

from utils import statsd_helper


@statsd_helper.statsd_timer('test')
def test_function():
    return 100


class StatsdHelperTestCase(unittest.TestCase):
    fake_time_call_count = 1
    mock_called = False

    @mock.patch('utils.statsd_helper.statsd.timing')
    @mock.patch('utils.statsd_helper.time')
    def test_mandatory_email(self, time_mock, statsd_timing_mock):
        def fake_time():
            if self.fake_time_call_count == 1:
                self.fake_time_call_count += 1
                return 1402523052.417958
            elif self.fake_time_call_count == 2:
                return 1402523052.818079

        time_mock.time.side_effect = fake_time

        def statsd_timing(name, time_ms):
            self.assertEqual(name, 'test.test_function')
            self.assertEqual(time_ms, 400)
            self.mock_called = True

        statsd_timing_mock.side_effect = statsd_timing

        self.assertFalse(statsd_timing_mock.called)

        result = test_function()
        self.assertEqual(result, 100)

        self.assertTrue(self.mock_called)
